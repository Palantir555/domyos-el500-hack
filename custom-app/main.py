#!/usr/bin/python3
import gatt
import signal
import asyncio
import threading
import coloredlogs
import numpy as np
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

# A thread-safe variable that helps the BLE connection handling thread to signal
# the EL500 logic thread that a connection is currently established:
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

    def start(self):
        logger.info("Starting BLE management thread")
        self.manager.start_discovery()
        self.manager_thread = threading.Thread(target=self.manager.run)
        self.manager_thread.start()
        logger.info("Awaiting connection to the El500")
        ble_connected.wait()
        if el500_ble_device is not None:
            logger.info("Connected to EL500")
            logger.info("Starting EL500 logic")
            self.logic()

    def session_logic(self):
        async def cmd(cmd, payload=None):
            resp = El500Cmd.send(cmd, payload, timeout=0.5)

        async def event_300ms(cmd_lock):
            while not kill_all_threads:
                async with cmd_lock:
                    await cmd(El500Cmd.getStatus)
                await asyncio.sleep(0.3)  # 300 ms

        async def event_1000ms(cmd_lock):
            def setdisplay_payload():
                return El500Cmd.build_setdisplay_payload(
                    displaymode=counter,  # El500Cmd.numdisplaymodes["distance"],
                    distance=counter,  # (tog * 1),
                    Kmph=counter,  # (tog * 2),
                    rpm=counter,  # (tog * 3),
                    resistance=counter & 0x0F,  # ((tog + 1) * 2),
                    heartrate=counter,  # (tog * 5),
                    kcal=counter,  # (tog * 6),  # Displayed as calories?? 1kcal/10sec moving!!
                )

            counter = np.uint8(0)
            tog = 0x00
            try:
                while not kill_all_threads:
                    async with cmd_lock:
                        await cmd(El500Cmd.setDisplay, setdisplay_payload())
                    await asyncio.sleep(1)  # 1000 ms
                    tog = 0x01 if tog == 0x00 else 0x00
                    counter += 1
            except Exception as e:
                logger.error(
                    "Exception in logic", exc_info=(type(e), e, e.__traceback__)
                )
                logger.error(e)

        async def event_4000ms(cmd_lock):
            def setinfo_payload():
                return El500Cmd.build_setinfo_payload(
                    kmph=counter,  # (tog + 2) * 3,
                    resistance=counter & 0x0F,  # (tog + 1),
                    inclinepercent=counter,  # (tog * 7),
                    mwatt=counter,  # ((tog + 1) * 5),
                    heartrateledcolor=counter,  # (tog),
                    btledswitch=counter,  # (tog),
                )

            counter = np.uint8(0)
            tog = 0x00
            try:
                while not kill_all_threads:
                    async with cmd_lock:
                        await cmd(El500Cmd.setInfoValue, setinfo_payload())
                    await asyncio.sleep(4)  # 4000 ms
                    tog = 0x01 if tog == 0x00 else 0x00
                    counter += 1
            except Exception as e:
                logger.error(
                    "Exception in logic", exc_info=(type(e), e, e.__traceback__)
                )
                logger.error(e)

        async def logic():
            try:
                cmd_lock = asyncio.Lock()
                # Run both events concurrently using asyncio.gather
                tasks = asyncio.gather(
                    event_300ms(cmd_lock),
                    event_1000ms(cmd_lock),
                    event_4000ms(cmd_lock),
                    return_exceptions=True,
                )
                await tasks
            except KeyboardInterrupt:
                tasks.cancel()

        # Run the main function using the asyncio event loop
        asyncio.run(logic())

    def logic(self):
        # Wait for the discovery process to finish
        ble_attributes_discovered.wait()
        # Send a startup sequence as extracted from the replay attack. less redundant
        time.sleep(0.5)  # Avoid timeout in the first command
        for cmd, payload in El500Cmd.startup_cmds():
            try:
                resp = El500Cmd.send(cmd, payload, attempts=4)
            except TimeoutError:
                logger.error(f"Timeout while sending command {cmd}: {payload}")
        # Replay the getStatus setDisplay commands, sprinkle some setInfoValue
        self.session_logic()
        # Disconnect BLE
        self.stop()


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
    # Names extracted from the decompiled android app:
    # FTMS_CLIENT_CONFIGURATION_UUID = "00002902-0000-1000-8000-00805F9B34FB"
    # FTMS_MACHINE_STATUS_UUID       = "00002ADA-0000-1000-8000-00805F9B34FB"
    # FTMS_MACHINE_FEATURE_UUID      = "00002ACC-0000-1000-8000-00805F9B34FB"
    # FTMS_ROWER_DATA_UUID           = "00002AD1-0000-1000-8000-00805F9B34FB"
    # FTMS_TREADMILL_DATA_UUID       = "00002ACD-0000-1000-8000-00805F9B34FB"
    # FTMS_ELLIPTICAL_DATA_UUID      = "00002ACE-0000-1000-8000-00805F9B34FB"
    # FTMS_BIKE_DATA_UUID            = "00002AD2-0000-1000-8000-00805F9B34FB"
    # FTMS_UUID                      = "00001826-0000-1000-8000-00805F9B34FB"
    # DEVICE_INFORMATION_UUID        = "0000180A-0000-1000-8000-00805F9B34FB"
    # SERVICE_UUID                   = "49535343-FE7D-4AE5-8FA9-9FAFD205E455"
    # WRITE_UUID                     = "49535343-8841-43F4-A8D4-ECBE34729BB3"
    # NOTIFY_UUID                    = "49535343-1E4D-4BD9-BA61-23C647249616"


class El500Cmd:
    headerByte = b"\xF0"  # Start of cmd. End of cmd is a checksum byte
    getStatus = b"\xAC"  # called non-stop
    setDisplay = b"\xCB"  # called every second
    setInfoValue = b"\xAD"  # called to set the device's state

    getEquipmentId = b"\xC9"
    getSerialNumber = b"\xA4"
    getVersion = b"\xA3"
    setSessionData = b"\xC4"  # 1 byte payload, app accepts only 3 or 255
    getUsageHours = b"\xA5"
    setFanSpeed = b"\xCA"
    setHotKey = b"\xC8"
    getCumulativeKm = b"\xAB"

    numdisplaymodes = {
        "off": 0,
        "distance": 1,  # TODO: miles or km?
        "scroll_good": 2,
        "distance": 3,  # TODO: miles or km?
        "off?": 4,
        "off??": 5,
        "off???": 6,
        "off????": 7,
        "reversingnow": 1,
    }  # TODO: complete: speed, heartrate, time

    uiheartcolor = {
        "off": 0,
        "blue": 1,
        "green": 2,
        "yellow": 3,
        "orange": 4,
        "red": 5,
    }

    @staticmethod
    def startup_cmds():
        # TODO: This function is a temporary hack to get sessions started. Move it elsewhere
        setInfoInitPayload = b"\xff\xff\xff\xff\xff\xff\xff\xff\x01\xff\xff\xff"
        setInfoInitPayload += b"\xff\xff\xff\xff\x01\xff\xff\xff"
        sessInitState = b"\x02\x00\x08\xff\x01\x00\x00\x01\x01\x00\x00\x00\x01"
        sessInitState += b"\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        sessInitStat2 = b"\x01\x00\x00\x02\x01\x00\x00\x01\x01\x00\x00\x00\x01"
        sessInitStat2 += b"\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        return [
            (El500Cmd.getEquipmentId, None),
            (El500Cmd.getSerialNumber, None),
            (El500Cmd.getVersion, None),
            (El500Cmd.setSessionData, b"\x03"),
            (El500Cmd.setInfoValue, setInfoInitPayload),
            (El500Cmd.setInfoValue, setInfoInitPayload),
            (El500Cmd.setInfoValue, setInfoInitPayload),
            (El500Cmd.setDisplay, sessInitState),
            (El500Cmd.getUsageHours, None),
            (El500Cmd.getStatus, None),
            (El500Cmd.setFanSpeed, b"\x00"),
            (El500Cmd.setHotKey, b"\x01"),
            (El500Cmd.getCumulativeKm, None),
            (El500Cmd.getStatus, None),
            (El500Cmd.setDisplay, sessInitStat2),
        ]

    @staticmethod
    def send(cmd_id, payload=None, timeout=1, attempts=1):
        # Create full command
        cmd = bytearray()
        cmd.extend(El500Cmd.headerByte)
        cmd.extend(bytearray(cmd_id))
        cmd.extend(bytearray(payload)) if payload is not None else None
        cmd.append(El500Cmd.checksum(cmd))
        logger.info(f" Sending -> {bin2hex(cmd)}")
        el500_ble_device.write(El500Characts.comms_AppToDev, cmd)
        while attempts > 0 and not kill_all_threads:
            attempts -= 1
            try:
                char, resp = El500Cmd.await_resp(timeout)
                return resp
            except TimeoutError as e:
                logger.warning(e)

    @staticmethod
    def await_resp(timeout=0.25):
        start = time.time()
        while not kill_all_threads:
            try:
                notif_charact, notif_value = ble_notifications_q.get(timeout=timeout)
                logger.info(f"Received <- {bin2hex(notif_value)}")
                return notif_charact, notif_value
            except queue.Empty:
                if timeout > 0 and time.time() - start > timeout:
                    raise TimeoutError("Timeout while waiting for notification")

    @staticmethod
    def checksum(data):
        chksum = 0
        for byte in data:
            chksum += byte
        return chksum & 0xFF

    @staticmethod
    def build_setdisplay_payload(
        displaymode, distance, Kmph, rpm, resistance, heartrate, kcal
    ):
        p = bytearray()
        # reversing the first 3 bytes of the message:
        # p.extend(b"\x01\x02\x30") # distance must be in here??
        # p.extend(b"\x01\x02\x20") # lowering byte2 lowers distance in device slightly
        # p.extend(b"\x01\x01\x30") # lowering byte1 lowers distance in device more
        # p.extend(b"\x00\x02\x30") # setting byte0=0 disables distance/time/heartrate display
        # p.extend(b"\x02\x02\x30") # setting byte0=2 scrolls 'GOOd' on the display
        # p.extend(b"\x01\x00\x00") # setting bytes1and2=0 , distance == 0!!
        p.extend(np.int8(displaymode).tobytes())
        p.extend(
            np.int16(distance).newbyteorder(">").tobytes()
        )  # TODO: meters? revolutions?
        p.extend(b"\x02\x01")
        p.extend(np.int16(Kmph).newbyteorder(">").tobytes())
        p.extend(b"\x01\x01")
        p.extend(np.int16(heartrate).newbyteorder(">").tobytes())
        p.extend(b"\x00\x01")
        p.extend(np.int16(rpm).newbyteorder(">").tobytes())
        p.extend(b"\x00\x01")
        p.extend(np.int16(kcal).newbyteorder(">").tobytes())
        p.extend(b"\x00\x01")
        p.extend(
            np.int16(resistance).newbyteorder(">").tobytes()
        )  # int8 in getStatus resp??
        p.extend(b"\x00")
        return p

    @staticmethod
    def build_setinfo_payload(
        kmph, resistance, inclinepercent, mwatt, heartrateledcolor, btledswitch
    ):
        # All bytes reversed from app
        p = bytearray()
        p.extend(b"\xff" * 2)
        p.extend(np.int8(kmph // 256).newbyteorder(">").tobytes())
        p.extend(np.int8(kmph % 256).newbyteorder(">").tobytes())
        p.extend(b"\xff" * 4)
        p.extend(np.int8(resistance).newbyteorder(">").tobytes())
        p.extend(b"\xff" * 2)
        p.extend(np.int8(inclinepercent // 256).newbyteorder(">").tobytes())
        p.extend(np.int8(inclinepercent % 256).newbyteorder(">").tobytes())
        p.extend(np.int8(mwatt // 256).newbyteorder(">").tobytes())
        p.extend(np.int8(mwatt % 256).newbyteorder(">").tobytes())
        p.extend(np.int8(heartrateledcolor).newbyteorder(">").tobytes())
        p.extend(np.int8(btledswitch).newbyteorder(">").tobytes())
        p.extend(b"\xff" * 3)
        return p


class BleDeviceManager(gatt.DeviceManager):
    known_devices = (
        set()
    )  # TODO high: Shouldn't be here, but this is a faux-singleton, so whatever

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
                    f"Enabling notifications for [{self.mac_address}] "
                    + f"\t\tCharacteristic [{charac.uuid}]"
                )
                charac.enable_notifications()  # "Subscribe" to all notifications
                # TODO: I only need to subscribe to the DevToApp characteristic
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

    # New:
    try:
        logic = ReversingLogic()
        logic.start()
    finally:
        logic.stop()
