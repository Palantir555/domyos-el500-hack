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
import enum

ble_vendor_id = "e8:5d:86"  # chang-yow.com.tw
target_el500_mac = f"{ble_vendor_id}:bf:35:9d"  # Target BLE Device (The real EL500)

kill_all_threads = False

el500_ble_device = None

# a thread-safe variable that helps the BLE connection handling thread to signal the EL500 logic thread that a connection is currently established:
ble_connected = threading.Event()
ble_attributes_discovered = threading.Event()
ble_notifications_q = queue.Queue(maxsize=100)

# Create a new logger for our threads. It prints all messages to stdout
logger = logging.getLogger("jc_logger")
ble_logger = logging.getLogger("ble_logger")
# logger for colored logs
coloredlogs.install(
    level="DEBUG",
    logger=logger,
    fmt="%(levelname)s %(message)s",  # %(asctime)s ?
    level_styles={
        "debug": {"color": "green"},
        "info": {"color": "green"},
        "error": {"color": "red"},
    },
)
# Serial logger messages should be green
coloredlogs.install(
    level="DEBUG",
    logger=ble_logger,
    fmt="%(levelname)s %(message)s",
    level_styles={
        "debug": {"color": "yellow"},
        "info": {"color": "yellow"},
        "error": {"color": "red"},
    },
)


class ReversingLogic:
    def __init__(self):
        self.manager = BleDeviceManager(adapter_name="hci0")

    def stop(self):
        if ble_connected.is_set():
            logger.info("Disconnecting from EL500")
            el500_ble_device.disconnect()
            time.sleep(0.19)  # give it some time
        self.manager.stop()

    def start_ble_manager(self):
        logger.info("Scanning for BLE devices...")
        self.manager.start_discovery()
        self.manager_thread = threading.Thread(target=self.manager.run)
        self.manager_thread.start()

    def start(self):
        self.start_ble_manager()
        # while not kill_all_threads:
        ble_connected.wait()
        if el500_ble_device is not None:
            logger.info("Connected to EL500")
            logger.info("Starting EL500 logic")
            self.logic()

    def logic(self):
        ble_attributes_discovered.wait()
        logger.info(f"Sending startup message {El500Cmd.cmdid_atd_startup}")
        if ble_connected.is_set() and ble_attributes_discovered.is_set():
            el500_ble_device.write(
                El500Attributes.CHARACT_STATES, El500Cmd.cmdid_atd_startup
            )
        while not kill_all_threads:
            try:
                notif_charact, notif_value = ble_notifications_q.get(timeout=1)
                break
            except queue.Empty:
                pass
        self.stop()


class El500Attributes:
    SERVICE_METADATA = "0000180a-0000-1000-8000-00805f9b34fb"
    CHARACT_META_0 = "00002a29-0000-1000-8000-00805f9b34fb"  # R:R:value-str="ISSC"
    # char ch0_val[] = "ISSC";
    CHARACT_META_1 = "00002a24-0000-1000-8000-00805f9b34fb"  # R:R:value-str="BM70"
    # char ch1_val[] = "BM70";
    CHARACT_META_2 = "00002a25-0000-1000-8000-00805f9b34fb"  # R:R:value-str="0000"
    # char ch2_val[] = "0000";
    CHARACT_META_3 = (
        "00002a27-0000-1000-8000-00805f9b34fb"  # R:R:value-str="5505 102_BLDK3"
    )
    # char ch3_val[] = "5505 102_BLDK3";
    CHARACT_META_4 = "00002a26-0000-1000-8000-00805f9b34fb"  # R:R:value-str="009500"
    # char ch4_val[] = "009500";
    CHARACT_META_5 = "00002a28-0000-1000-8000-00805f9b34fb"  # R:R:value-str="0000"
    # char ch5_val[] = "0000";
    CHARACT_META_6 = (
        "00002a23-0000-1000-8000-00805f9b34fb"  # R:R:value="0000000000000000"
    )
    # uint8_t ch6_val[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    CHARACT_META_7 = (
        "00002a2a-0000-1000-8000-00805f9b34fb"  # R:R:value="0000000001000000"
    )
    # uint8_t ch7_val[] = {0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00};

    SERVICE_UNKNOWN_0 = "49535343-5d82-6099-9348-7aac4d5fbc51"
    CHARACT_UNK0_0 = "49535343-026e-3a9b-954c-97daef17e26e"  # W:W/N
    # BLE2902 descrCharUnk0;
    SERVICE_UNKNOWN_1 = "49535343-c9d0-cc83-a44a-6fe238d06d33"
    CHARACT_UNK1_0 = "49535343-aca3-481c-91ec-d85e28a60318"  # W:W/N
    # BLE2902 descrCharUnk1;
    SERVICE_STATEREPORTS = "49535343-fe7d-4ae5-8fa9-9fafd205e455"
    CHARACT_STATES = "49535343-1e4d-4bd9-ba61-23c647249616"  # W:W/WnR/N
    # BLE2902 descrCharStateStates;
    CHARACT_ST_1 = "49535343-8841-43f4-a8d4-ecbe34729bb3"  # W:W/WnR/N
    CHARACT_ST_2 = "49535343-4c8a-39b3-2f49-511cff073b7e"  # W:W/N
    # BLE2902 descrCharStateSt2;


class El500Cmd:
    cmdid_atd_startup = b"\xf0\xc9\xb9"  # App to Device
    cmdid_dta_status = b"\xf0\xbc"  # Device to App


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


class BleDeviceManager(gatt.DeviceManager):
    known_devices = (
        set()
    )  # TODO high: Shouldn't be here, but this is a faux-singleton, so whatever...
    # This function is called when a BLE device is discovered
    def device_discovered(self, device):
        global el500_ble_device  # TODO: remove this shitty global
        if device.mac_address.lower() == target_el500_mac.lower():
            ble_logger.info(
                f"Target discovered: [{device.mac_address}] {device.alias()}"
            )
            el500_ble_device = BleConnectionHandler(
                mac_address=device.mac_address, manager=self
            )
            self.stop_discovery()
            el500_ble_device.connect()
        elif device.mac_address not in self.known_devices:
            ble_logger.debug(f"Discovered [{device.mac_address}] {device.alias()}")
            self.known_devices.add(device.mac_address)


class BleConnectionHandler(gatt.Device):
    """Represents a Domyos EL500 eliptical training machine. It uniquely
    identifies a BLE server, manages our BLE connection to it, and provides a
    high-level interface to the machine."""

    # JC's API:
    def write(self, char_uuid, data):
        """Write data to a characteristic."""
        for s in self.services:
            for c in s.characteristics:
                if str(c.uuid) == char_uuid:
                    ble_logger.debug(f"Writing to {char_uuid}: {data}")
                    c.write_value(data)
                    return
        ble_logger.error(f"Characteristic {char_uuid} not found")

    # Parent class' API
    def connect_succeeded(self):
        super().connect_succeeded()
        ble_connected.set()
        ble_logger.info(f"[{self.mac_address}] Connected")

    def connect_failed(self, error):
        super().connect_failed(error)
        ble_connected.clear()
        ble_logger.info(f"[{self.mac_address}] Connection failed: {str(error)}")

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        ble_attributes_discovered.clear()
        ble_connected.clear()
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
        ble_attributes_discovered.set()

    def characteristic_value_updated(self, characteristic, value):
        """This is the callback for when a notification is received"""
        # serial_msg = bytes(f"Notify,{characteristic.uuid},{value.hex()}\r\n", "utf-8")
        ble_logger.info(f"Notified[{characteristic.uuid}][{value}]")  # - {serial_msg}"
        ble_notifications_q.put_nowait((characteristic, value))
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
    """This function is called when the user presses Ctrl+C"""
    global kill_all_threads
    logger.info("Exiting...")
    logic.stop()
    kill_all_threads = True
    sys.exit(0)


if __name__ == "__main__":
    print("Hello World")

    # configure sigint handler:
    signal.signal(signal.SIGINT, sigint_handler)

    # Start the BLE manager:
    # manager = BleDeviceManager(adapter_name="hci0")
    # manager.start_discovery()
    # manager.run()

    # New:
    logic = ReversingLogic()
    logic.start()
