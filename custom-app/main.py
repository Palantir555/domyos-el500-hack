#!/usr/bin/python3
import gatt
import signal
import asyncio
import threading
import coloredlogs
import logging
import queue
import time
import sys
import re
import enum
import el500mitmlogs
from kaitaistruct import KaitaiStream, BytesIO

# kaitai-struct-compiler -t python message_structs.ksy
from response_status import ResponseStatus

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
        "warning": {"color": "yellow"},
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

# Disable ble_logger for now
ble_logger.disabled = True


def bin2hex(binmsg):
    return " ".join(f"{byte:02x}" for byte in binmsg)


class ReversingLogic:
    def __init__(self):
        self.manager = BleDeviceManager(adapter_name="hci0")

    def stop(self):
        self.manager.stop()
        if ble_connected.is_set():
            logger.info("Disconnecting from EL500")
            el500_ble_device.disconnect()
            time.sleep(0.19)  # give it some time

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

    def write_chunked(self, data, chunk_size=20, overwrite_last_byte=True):
        def set_chunk_count_octet():  # TODO dirty dirty hack. The original 'data' shouldn't include the terminator byte; it should be dynamically generated instead. I just don't yet fully understand how
            n_chunks = len(range(0, len(data), chunk_size))
            cmd_byte = data[1]
            first_octet = (cmd_byte & 0xF0) >> 4
            second_octet = cmd_byte & 0x0F
            first_octet = (first_octet - n_chunks) & 0x0F
            modified_last_byte = (first_octet << 4) | second_octet
            return data[:-1] + bytes([modified_last_byte])

        data = set_chunk_count_octet()

        for i in range(0, len(data), chunk_size):
            msg = data[i : i + chunk_size]
            logger.info(f" Sending -> {bin2hex(msg)}")
            el500_ble_device.write(El500Characts.comms_AppToDev, msg)
            time.sleep(0.3)

    def interactive_logic(self):
        ASK_BEFORE_WRITE = False

        # mitm_clean_logs = "mitm_clean.log"
        mitm_clean_logs = "mitm_new.tsv"
        with open(mitm_clean_logs, "r") as f:
            conversation = el500mitmlogs.parse_tsvconversation(f.read())
        for cmd, response in conversation:
            if cmd is None:
                continue
            if ASK_BEFORE_WRITE is True:
                inp = input(f"Send cmd ?? {bin2hex(cmd)}? [Y/n]")
                if inp.lower() in ["n", "no"]:
                    continue
            # self.write_chunked(cmd) # This overwrites the last byte, which we need to replay. Even if that's worked around, the chunking itself causes problems (not receiving some expected notifications). TODO: figure out why, as it is probably messing with the dynamically generated chunked messages
            logger.info(f" Sending -> {bin2hex(cmd)}")
            el500_ble_device.write(El500Characts.comms_AppToDev, cmd)
            try:
                char, msg = ReversingLogic.await_notification(timeout=3)
            except TimeoutError:
                logger.warning("Timeout while waiting for response")
                char, msg = None, None
            if msg != response:
                logger.warning(
                    f"Expected <- {bin2hex(response) if response is not None else None}"
                )
                logger.warning(
                    f"Received <- {bin2hex(msg) if msg is not None else None}"
                )
            else:
                logger.info(f"Received <- {bin2hex(msg) if msg is not None else None}")

    def session_logic(self):
        async def send_data(data):
            self.write_chunked(data, overwrite_last_byte=False)

        async def receive_data():
            try:
                char, msg = ReversingLogic.await_notification(1)
                logger.info(f"Received <- {bin2hex(msg)}")
            except TimeoutError:
                logger.warning(f"Received <- TIMEOUT")
                char, msg = None, None

        async def event_300ms(cmd_lock):
            while not kill_all_threads:
                async with cmd_lock:
                    await send_data(El500Cmd.getStatus)
                    await receive_data()
                await asyncio.sleep(0.3)  # 300 ms

        async def event_1000ms(cmd_lock):
            def build_setSessionState_msg():
                return El500Cmd.setSessionState

            while not kill_all_threads:
                async with cmd_lock:
                    await send_data(build_setSessionState_msg())
                    await receive_data()
                await asyncio.sleep(1)  # 1000 ms

        async def logic():
            try:
                cmd_lock = asyncio.Lock()
                # Run both events concurrently using asyncio.gather
                tasks = asyncio.gather(
                    event_300ms(cmd_lock),
                    event_1000ms(cmd_lock),
                    return_exceptions=True,
                )
                await tasks
            except KeyboardInterrupt:
                tasks.cancel()

        # Run the main function using the asyncio event loop
        asyncio.run(logic())

    def logic(self):
        def parse_status_msg(binmsg):
            return ResponseStatus.from_bytes(binmsg)

        # TODO: If the target is disconnected, restart the logic(?)
        ble_attributes_discovered.wait()

        # Replays the start of the conversation hoping to start a session (TODO: Reverse this)
        self.interactive_logic()

        # Replay the getStatus setSession commands
        self.session_logic()

        self.stop()

    @staticmethod
    def await_notification(timeout=0):
        start = time.time()
        while not kill_all_threads:
            try:
                notif_charact, notif_value = ble_notifications_q.get(timeout=0.25)
                return notif_charact, notif_value
            except queue.Empty:
                if timeout > 0 and time.time() - start > timeout:
                    raise TimeoutError("Timeout while waiting for notification")


class El500ServiceUuids:
    METADATA = "0000180a-0000-1000-8000-00805f9b34fb"
    UNKNOWN_0 = "49535343-5d82-6099-9348-7aac4d5fbc51"
    UNKNOWN_1 = "49535343-c9d0-cc83-a44a-6fe238d06d33"
    COMMS = "49535343-fe7d-4ae5-8fa9-9fafd205e455"


class El500Characts:
    meta0 = "00002a29-0000-1000-8000-00805f9b34fb"  # R:R:value-str="ISSC"
    meta1 = "00002a24-0000-1000-8000-00805f9b34fb"  # R:R:value-str="BM70"
    meta2 = "00002a25-0000-1000-8000-00805f9b34fb"  # R:R:value-str="0000"
    meta3 = "00002a27-0000-1000-8000-00805f9b34fb"  # R:R:value-str="5505 102_BLDK3"
    meta4 = "00002a26-0000-1000-8000-00805f9b34fb"  # R:R:value-str="009500"
    meta5 = "00002a28-0000-1000-8000-00805f9b34fb"  # R:R:value-str="0000"
    meta6 = "00002a23-0000-1000-8000-00805f9b34fb"  # R:R:value="0000000000000000"
    meta7 = "00002a2a-0000-1000-8000-00805f9b34fb"  # R:R:value="0000000001000000"
    UNK0_0 = "49535343-026e-3a9b-954c-97daef17e26e"  # W:W/N + Descriptor BLE2902
    UNK1_0 = "49535343-aca3-481c-91ec-d85e28a60318"  # W:W/N + BLE2902
    comms_DevToApp = "49535343-1e4d-4bd9-ba61-23c647249616"  # W:W/WnR/N + BLE2902
    comms_AppToDev = "49535343-8841-43f4-a8d4-ecbe34729bb3"  # W:W/WnR/N
    comms_unknown = "49535343-4c8a-39b3-2f49-511cff073b7e"  # W:W/N + BLE2902


class El500Cmd:
    # startup = b"\xf0\xc9\xb9"
    # ready = b"\xf0\xc4\x03\xb7"
    # wat = b"\xf0\xad\xff\xff\xff\xff\xff\xff\xff\xff\x01\xff\xff\xff\xff\xff\xff\xff\x01\xff\xff\xff\x8d"
    getStatus = b"\xf0\xac\x9c"
    setSessionState = b"\xf0\xcb\x01\x02\x30\x02\x01\x00\x38\x01\x01\x00\x59\x00\x01\x00\x41\x00\x01\x00\x02\x00\x01\x00\x07\x00\xd1"  # Captured terminator byte: "\xca"


class SerialOverBle:
    rx_char_uuid = El500Characts.comms_DevToApp
    tx_char_uuid = El500Characts.comms_AppToDev

    def __init__(self, rx_msg_q):
        self.rx_buffer = bytearray()
        self.rx_msg_q = rx_msg_q

    # def notification_handler(self, data):
    #     # if a notification is received, and it's 20-bytes long, add it to the rx buffer.
    #     # If it is under 20 bytes, it is the last packet of a message, so add it to the
    #     # buffer and put the buffer into the rx queue.
    #     if len(data) == 20:
    #         self.rx_buffer += data
    #     elif len(data) > 20:
    #         raise ValueError(
    #             "Received a notification longer than 20 bytes. "
    #             + "Although this was expected? I think this can be removed safely"
    #         )
    #     else:
    #         self.rx_buffer += data
    #         self.rx_msg_q.put(self.rx_buffer)
    #         self.rx_buffer = bytearray()

    def write(self, data):
        # el500_ble_device.write(self.tx_char_uuid, data)
        # split the message into 20 byte chunks, and write them:
        for i in range(0, len(data), 20):
            el500_ble_device.write(self.tx_char_uuid, data[i : i + 20])


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
                    ble_logger.debug(f"Writing[{char_uuid}][{bin2hex(data)}]")
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
        ble_logger.info(f"Notified[{characteristic.uuid}][{bin2hex(value)}]")
        ble_notifications_q.put_nowait((characteristic, value))
        # ble_logger.debug(serial_msg)

    def characteristic_write_value_succeeded(self, characteristic):
        # ble_logger.debug("characteristic_write_value_succeeded")
        pass

    def characteristic_write_value_failed(self, characteristic, error):
        ble_logger.error("characteristic_write_value_failed")
        # TODO: I think the app would retry here, but I don't have the value to retry with ATM

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
    # configure sigint handler:
    signal.signal(signal.SIGINT, sigint_handler)

    # Start the BLE manager:
    # manager = BleDeviceManager(adapter_name="hci0")
    # manager.start_discovery()
    # manager.run()

    # New:
    try:
        logic = ReversingLogic()
        logic.start()
    finally:
        logic.stop()
