#!/usr/bin/python3
import gatt
import serial
import signal
import threading
import queue
import logging
import time
import sys
import re

# import module for colorful logging
import coloredlogs

# Target BLE Device (The real EL500)
target_el500_mac = "e8:5d:86:bf:35:9d"  # My EL500's MAC address
TARGET_MAC = target_el500_mac

EL500_SPOOFER_SERIALPORT = "/dev/ttyUSB0"
EL500_SPOOFER_BAUDRATE = 230400  # 115200

el500_ble_device = None
serial_output_queue = queue.Queue()

kill_all_threads = False

# Create a new logger for our threads. It prints all messages to stdout
logger = logging.getLogger("jc_logger")
serial_logger = logging.getLogger("serial_logger")
ble_logger = logging.getLogger("ble_logger")
# logger debug messages should be printed in red
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(levelname)s %(message)s",  # %(asctime)s ?
    level_styles={"debug": {"color": "green"}, "error": {"color": "red"}},
)
# Serial logger messages should be yellow
coloredlogs.install(
    level="DEBUG",
    logger=serial_logger,
    fmt="%(levelname)s %(message)s",
    level_styles={
        "debug": {"color": "yellow"},
        "info": {"color": "yellow"},
        "error": {"color": "red"},
    },
)
# Serial logger messages should be green
coloredlogs.install(
    level="DEBUG",
    logger=ble_logger,
    fmt="%(levelname)s %(message)s",
    level_styles={
        "debug": {"color": "green"},
        "info": {"color": "green"},
        "error": {"color": "red"},
    },
)
# initialize the logger
# logger.setLevel(logging.DEBUG)
# Configure logger to print debug messages darker than INFO:
# logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def b2hex(bytestring):
    return " ".join(format(b, "02x") for b in bytestring)


class MyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        global el500_ble_device
        # logger.debug(f"Discovered [{device.mac_address}] {device.alias()}")
        if device.mac_address.lower() == TARGET_MAC.lower():
            ble_logger.info(
                f"Target discovered: [{device.mac_address}] {device.alias()}"
            )
            el500_ble_device = Target(mac_address=device.mac_address, manager=self)
            el500_ble_device.connect()


class Target(gatt.Device):
    def connect_succeeded(self):
        super().connect_succeeded()
        ble_logger.info(f"[{self.mac_address}] Connected")

    def connect_failed(self, error):
        super().connect_failed(error)
        ble_logger.info(f"[{self.mac_address}] Connection failed: {str(error)}")

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        ble_logger.info(f"[{self.mac_address}] Disconnected")

    def services_resolved(self):
        super().services_resolved()

        ble_logger.debug(f"[{self.mac_address}] Resolved services")
        for service in self.services:
            ble_logger.debug(f"[{self.mac_address}] \tService [{service.uuid}]")
            for charac in service.characteristics:
                ble_logger.debug(
                    f"Enabling notifications for [{self.mac_address}] \t\tCharacteristic [{charac.uuid}]"
                )
                charac.enable_notifications()  # Subscribe to all notifications
                # charac.write_value(b'\x42\x41\x43') # just testing
                # JC: This version of the gatt lib doesn't seem to support descriptors??
                # for descr in charac.descriptors:
                #     ble_logger.debug(f"[{self.mac_address}]\t\t\tDescriptor [{descr.uuid}] ({descr.read_value()})")

    def characteristic_value_updated(self, characteristic, value):
        """This is the callback for when a notification is received"""
        global serial_output_queue
        serial_msg = bytes(f"Notify,{characteristic.uuid},{value.hex()}\r\n", "utf-8")
        ble_logger.info(
            f"Target to App: Notify[{characteristic.uuid}][{b2hex(value)}]"  # - {serial_msg}"
        )
        # ble_logger.debug(serial_msg)
        serial_output_queue.put(
            serial_msg
        )  # Move fstring into generic serialize_command(cmd, uuid, value)

    def characteristic_write_value_succeeded(self, characteristic):
        # ble_logger.debug("characteristic_write_value_succeeded")
        pass

    def characteristic_write_value_failed(self, characteristic, error):
        ble_logger.error("characteristic_write_value_failed")

    def characteristic_read_value_succeeded(self, characteristic, value):
        ble_logger.debug("characteristic_read_value_succeeded")

    def characteristic_status_updated(self, characteristic, error):
        ble_logger.error(f"characteristic_status_updated {error}")

    def descriptor_read_value_failed(self, descriptor, error):
        ble_logger.error("descriptor_value_failed")


def serial_input_cback(dataline):
    """This function is called whenever a line of serial input is received. It
    should parse the data and call the appropriate BLE functions."""

    def write_handler(serial_msg):
        # Parse the input line with a regex. Format: "<command>[<characteristic>][<msg> ]\r\n"
        # Example: b'Write[:49535343-8841-43f4-a8d4-ecbe34729bb3][F0 C9 B9 ]\r\n'
        # Example: b'Read[49535343-8841-43f4-a8d4-ecbe34729bb3]\r\n'
        data = re.match(
            r"Write\[(?P<uuid>[0-9a-fA-F-]+)\]\[(?P<msg>[0-9a-fA-F ]+)\]\r\n",
            serial_msg.decode(),
        )
        if not data:
            serial_logger.error(f"Failed to parse {serial_msg.decode()}")
            return
        # if msg's datatype is not bytes, convert it to bytes:
        if (
            type(data.group("msg")) is not bytes
        ):  # TODO JC high: This might be very buggy!
            try:
                # Convert msg from "A0 B1 D2 " to a binary string:
                msg = bytes.fromhex(data.group("msg").replace(" ", ""))
            except ValueError:
                logger.error(f'Failed to parse message payload: {data.group("msg")}')
                return
        else:
            msg = data.group("msg")
        serial_logger.info(f'App to Target:  Write[{data["uuid"]}][{b2hex(msg)}]')
        # Write <msg> to <uuid>
        # Find BLE service and characteristic with the given UUID
        if el500_ble_device:
            for service in el500_ble_device.services:
                for charac in service.characteristics:
                    if charac.uuid == data["uuid"]:
                        # Write the message to the characteristic over BLE
                        charac.write_value(msg)

    def notify_handler(serial_msg):
        # Example: b'Notify[49535343-8841-43f4-a8d4-ecbe34729bb3][F0 C9 B9 ]\r\n'
        data = re.match(
            r"Notify\[(?P<uuid>[0-9a-fA-F-]+)\]\[(?P<msg>[0-9a-fA-F ]+)\]\r\n",
            serial_msg.decode(),
        )
        if not data:
            serial_logger.error(f"Failed to parse {dataline.decode()}")
            return
        # if msg's datatype is not bytes, convert it to bytes:
        if (
            type(data.group("msg")) is not bytes
        ):  # TODO JC high: This might be very buggy!
            try:
                # Convert msg from "A0 B1 D2 " to a binary string:
                msg = bytes.fromhex(data.group("msg").replace(" ", ""))
            except ValueError:
                serial_logger.error(
                    f'Failed to parse message payload: {data.group("msg")}'
                )
                return
        else:
            msg = data.group("msg")
        serial_logger.info(f'App to Target: Notify[{data["uuid"]}][{b2hex(msg)}]')
        # Write <msg> to <uuid>
        # Find BLE service and characteristic with the given UUID
        if el500_ble_device:
            for service in el500_ble_device.services:
                for charac in service.characteristics:
                    if charac.uuid == data["uuid"]:
                        # Notify the BLE device
                        charac.write_value(msg)

    def read_handler(serial_msg):
        # Parse the characteristic UUID
        data = re.match(r"Read\[(?P<uuid>[0-9a-fA-F-]+)\]\r\n", dataline.decode())
        if not data:
            serial_logger.error(f"Failed to parse {dataline.decode()}")
            return
        serial_logger.info(f"App to Target: Read[{uuid}]")
        # Find BLE service and characteristic with the given UUID
        if el500_ble_device:
            for service in el500_ble_device.services:
                for charac in service.characteristics:
                    if charac.uuid == uuid:
                        # read the real device's value over BLE
                        charvalue = charac.read_value()
                        ble_logger.info(f"BLE read response [{uuid}] = {charvalue}")
                        # Write the value to the serial port
                        serial_msg = f"ReadResponse,{uuid},{charvalue.hex()}\r\n"
                        serial_logger.info(f"Sending serial response: {serial_msg}")
                        serial_output_queue.put(bytes(serial_msg, "utf-8"))
                        return

    if dataline.startswith(b"Write"):
        write_handler(dataline)
    elif dataline.startswith(b"Read"):
        read_handler(dataline)
    elif dataline.startswith(b"Notify"):
        notify_handler(dataline)

    else:
        serial_logger.error(f"Unparsed serial input: {dataline}")


def serial_port_handler():
    """This function runs as a standalone thread. It constantly checks for serial
    input, parses it, and calls serial_input_cback(). If it receives a message
    over a thread-safe queue, it will send it to the serial port."""
    serial_logger.info(f"Connecting to serial port...")
    with serial.Serial(
        EL500_SPOOFER_SERIALPORT, EL500_SPOOFER_BAUDRATE, timeout=1
    ) as ser:
        logger.info(f"Commanding ESP32 reboot over serial...")
        ser.write(b"Restart,0,00\r\n")
    with serial.Serial(
        EL500_SPOOFER_SERIALPORT, EL500_SPOOFER_BAUDRATE, timeout=10
    ) as ser:
        logger.debug(
            f"Opened serial port {EL500_SPOOFER_SERIALPORT} at {EL500_SPOOFER_BAUDRATE} baud"
        )
        while True:
            if kill_all_threads:
                logger.info("Serial port handler thread exiting")
                return
            if ser.in_waiting:
                serial_input_cback(ser.readline())
            if not serial_output_queue.empty():
                ser.write(serial_output_queue.get())
            time.sleep(0.1)


def sigint_handler(sig, frame):
    """This function is called when the user presses Ctrl-C"""
    global kill_all_threads
    logger.info("Exiting...")
    # Disconnect from the BLE device
    if el500_ble_device:
        el500_ble_device.disconnect()
        time.sleep(0.19)  # give it some time
    kill_all_threads = True
    # kill all threads:
    serial_port_thread.join()
    sys.exit(0)


if __name__ == "__main__":
    # Start the serial port handler thread:
    serial_port_thread = threading.Thread(target=serial_port_handler, name="Serial")
    serial_port_thread.start()
    # serial_port_handler()

    # configure sigint handler:
    signal.signal(signal.SIGINT, sigint_handler)

    # Start the BLE manager:
    manager = MyDeviceManager(adapter_name="hci0")
    manager.start_discovery()
    manager.run()
