#!/usr/bin/python3
import gatt
import signal
import threading
import coloredlogs
import logging
import queue
import time
import sys
import re

ble_vendor_id = "e8:5d:86"  # chang-yow.com.tw
target_el500_mac = f"{ble_vendor_id}:bf:35:9d"  # Target BLE Device (The real EL500)

kill_all_threads = False

el500_ble_device = None

# Create a new logger for our threads. It prints all messages to stdout
logger = logging.getLogger("jc_logger")
ble_logger = logging.getLogger("ble_logger")
# logger debug messages should be printed in red
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(levelname)s %(message)s",  # %(asctime)s ?
    level_styles={"debug": {"color": "green"}, "error": {"color": "red"}},
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


class BleDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        global el500_ble_device
        # logger.debug(f"Discovered [{device.mac_address}] {device.alias()}")
        if device.mac_address.lower() == target_el500_mac.lower():
            ble_logger.info(
                f"Target discovered: [{device.mac_address}] {device.alias()}"
            )
            el500_ble_device = BleConnectionHandler(mac_address=device.mac_address, manager=self)
            el500_ble_device.connect()

class El500Cmd(object):
    cmdid_atd_startup = b'\xf0\xc9\xb9' # App to Device
    cmdid_dta_status = b'\xf0\xbc' # Device to App
    def __init__(self, ble_char, ble_msg):
        

class El500Status(object):
    def __init__(
        self,
        rpm_left,
        rpm_right,
        resistance,
        active_seconds,
        active_minutes,
        heart_rate,
    ):
        self.rpm_left = rpm_left
        self.rpm_right = rpm_right
        self.resistance = resistance
        self.active_seconds = active_seconds
        self.active_minutes = active_minutes
        self.heart_rate = heart_rate

    def set_from_ble_msg(self, msg):
        """Load BLE status msg byte array into the object properties. msg format:
        b'<cmd_id:2><unk0:2><unk1:2><rpm_left:2><rpm_right:2><active_sec:2><active_min:2><resistance:1><unk2:1><unk3:2><heart_rate:1><unk4:1>'
        """
        cmd_id = int.from_bytes(msg[0:2], byteorder="little", signed=False)
        unk0 = int.from_bytes(msg[2:4], byteorder="little", signed=False)
        unk1 = int.from_bytes(msg[4:6], byteorder="little", signed=False)
        self.rpm_left = int.from_bytes(msg[6:8], byteorder="little", signed=False)
        self.rpm_right = int.from_bytes(msg[8:10], byteorder="little", signed=False)
        self.active_seconds = int.from_bytes(
            msg[10:12], byteorder="little", signed=False
        )
        self.active_minutes = int.from_bytes(
            msg[12:14], byteorder="little", signed=False
        )
        self.resistance = int.from_bytes(msg[14:15], byteorder="little", signed=False)
        unk2 = int.from_bytes(msg[15:16], byteorder="little", signed=False)
        unk3 = int.from_bytes(msg[16:18], byteorder="little", signed=False)
        self.heartrate = int.from_bytes(msg[18:19], byteorder="little", signed=False)
        self.heartrate = int.from_bytes(msg[19:20], byteorder="little", signed=False)

    def __str__(self):
        return f"RPM: {self.rpm_left} / {self.rpm_right} | Resistance: {self.resistance} | Active: {self.active_minutes}m {self.active_seconds}s | Heart Rate: {self.heart_rate}"


class BleConnectionHandler(gatt.Device):
    """Represents a Domyos EL500 eliptical training machine. It uniquely
    identifies a BLE server, manages our BLE connection to it, and provides a
    high-level interface to the machine."""

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
        # serial_msg = bytes(f"Notify,{characteristic.uuid},{value.hex()}\r\n", "utf-8")
        # ble_logger.info(
        #     f"Target to App: Notify[{characteristic.uuid}][{value}]"  # - {serial_msg}"
        # )
        self.handle_notification(characteristic, value)
        # ble_logger.debug(serial_msg)

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


def sigint_handler(sig, frame):
    """This function is called when the user presses Ctrl-C"""
    global kill_all_threads
    logger.info("Exiting...")
    # Disconnect from the BLE device
    if el500_ble_device:
        el500_ble_device.disconnect()
        time.sleep(0.19)  # give it some time
    kill_all_threads = True
    sys.exit(0)


if __name__ == "__main__":
    print("Hello World")

    # configure sigint handler:
    signal.signal(signal.SIGINT, sigint_handler)

    # Start the BLE manager:
    manager = BleDeviceManager(adapter_name="hci0")
    manager.start_discovery()
    manager.run()
