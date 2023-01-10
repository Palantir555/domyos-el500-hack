import gatt
import serial
import threading
import queue
import logging
import time
import re
#import module for colorful logging
import coloredlogs

# Target BLE Device (The real EL500)
target_el500_mac = 'e8:5d:86:bf:35:9f' # My EL500's MAC address
SpOoFeR_MaC = 'e8:5d:86:bf:35:42' # esp32's spoofed mac address to look like a legit device - SHOULD NOT BE USED FROM THIS SCRIPT. The spoofer should connect to the mobile app, and this laptop's BLE should connect to the EL500 and spoof the behavior of the eConnected mobile app
TARGET_MAC = target_el500_mac

EL500_SPOOFER_SERIALPORT = '/dev/ttyUSB0'
EL500_SPOOFER_BAUDRATE = 115200

el500_ble_device = None
serial_output_queue = queue.Queue()

# Create a new logger for our threads. It prints all messages to stdout
logger = logging.getLogger('jc_logger')
# logger debug messages should be printed in red
coloredlogs.install(level='DEBUG', logger=logger, fmt='%(asctime)s %(levelname)s %(message)s',
                    level_styles={'debug': {'color': 'blue'}, 'error': {'color': 'red'}})
# initialize the logger
# logger.setLevel(logging.DEBUG)
# Configure logger to print debug messages darker than INFO:
# logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class MyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        global el500_ble_device
        # logger.debug(f"Discovered [{device.mac_address}] {device.alias()}")
        if device.mac_address.lower() == TARGET_MAC.lower():
            logger.info(f"Target discovered: [{device.mac_address}] {device.alias()}")
            el500_ble_device = Target(mac_address=device.mac_address, manager=self)
            el500_ble_device.connect()
            dir(el500_ble_device)

class Target(gatt.Device):
    def connect_succeeded(self):
        super().connect_succeeded()
        logger.info(f"[{self.mac_address}] Connected")

    def connect_failed(self, error):
        super().connect_failed(error)
        logger.info(f"[{self.mac_address}] Connection failed: {str(error)}")

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        logger.info(f"[{self.mac_address}] Disconnected")

    def services_resolved(self):
        super().services_resolved()

        logger.debug(f"[{self.mac_address}] Resolved services")
        for service in self.services:
            logger.debug(f"[{self.mac_address}] \tService [{service.uuid}]")
            for charac in service.characteristics:
                logger.debug(f"Enabling notifications for [{self.mac_address}] \t\tCharacteristic [{charac.uuid}]")
                charac.enable_notifications()
                # charac.write_value(b'\x42\x41\x43') # just testing
                # JC: This version of the gatt lib doesn't seem to support descriptors??
                # for descr in charac.descriptors:
                #     logger.debug(f"[{self.mac_address}]\t\t\tDescriptor [{descr.uuid}] ({descr.read_value()})")
        # subscribe to all characteristics
        for service in self.services:
            for charac in service.characteristics:
                charac.enable_notifications()

    def descriptor_read_value_failed(self, descriptor, error):
        logger.error('descriptor_value_failed')

def serial_input_cback(dataline):
    '''This function is called whenever a line of serial input is received. It
    should parse the data and call the appropriate BLE functions.'''
    # Parse the input line with a regex. Format: "<command>[char:<characteristic>][msg:<msg> ]\r\n"
    # Example: b'Write[char:49535343-8841-43f4-a8d4-ecbe34729bb3][msg:F0 C9 B9 ]\r\n'
    # Example: b'Read[char:49535343-8841-43f4-a8d4-ecbe34729bb3]\r\n'
    # Example: b'Notify[char:49535343-8841-43f4-a8d4-ecbe34729bb3][msg:F0 C9 B9 ]\r\n'
    if dataline.startswith(b'Write'):
        data = re.match(r'Write\[char:(?P<uuid>[0-9a-fA-F-]+)\]\[msg:(?P<msg>[0-9a-fA-F ]+)\]\r\n', dataline.decode())
        if not data:
            logger.error(f'Failed to parse {dataline.decode()}')
            return
        # Convert msg from "A0 B1 D2 " to a binary string:
        msg = bytes.fromhex(data.group('msg').replace(' ', ''))
        logger.info(f'Spoofer received app cmd: Write[{data["uuid"]}][{msg}]')
        # Write <msg> to <uuid>
        # Find BLE service and characteristic with the given UUID
        if el500_ble_device:
            for service in el500_ble_device.services:
                for charac in service.characteristics:
                    if charac.uuid == data['uuid']:
                        # Write the message to the characteristic over BLE
                        charac.write_value(msg)

    elif dataline.startswith(b'Read'):
        # Parse the characteristic UUID
        data = re.match(r'Read\[char:(?P<uuid>[0-9a-fA-F-]+)\]\r\n', dataline.decode())
        if not data:
            logger.error(f'Failed to parse {dataline.decode()}')
            return
        logger.info(f'Spoofer received app cmd: Read[{uuid}]')
        # Find BLE service and characteristic with the given UUID
        if el500_ble_device:
            for service in el500_ble_device.services:
                for charac in service.characteristics:
                    if charac.uuid == uuid:
                        # read the real device's value over BLE
                        charvalue = charac.read_value()
                        logger.debug(f'Got real device value [{uuid}] = {charvalue}')
                        # Write the value to the serial port
                        serial_msg = f'ReadResponse,{uuid},{charvalue.hex()}\r\n'
                        logger.info(f'Sending response over serial: {serial_msg}')
                        serial_output_queue.put(serial_msg)
                        return

    else:
        logger.debug(f'Unparsed serial input: {dataline}')

def serial_port_handler():
    '''This function runs as a standalone thread. It constantly checks for serial
    input, parses it, and calls serial_input_cback(). If it receives a message
    over a thread-safe queue, it will send it to the serial port.'''
    logger.info(f'Connecting to serial port...')
    with serial.Serial(EL500_SPOOFER_SERIALPORT, EL500_SPOOFER_BAUDRATE, timeout=1) as ser:
        logger.info(f'Opened serial port {EL500_SPOOFER_SERIALPORT} at {EL500_SPOOFER_BAUDRATE} baud')
        while True:
            if ser.in_waiting:
                serial_input_cback(ser.readline())
            if not serial_output_queue.empty():
                ser.write(serial_output_queue.get())
            time.sleep(0.1)

# Start the serial port handler thread:
serial_port_thread = threading.Thread(target=serial_port_handler, name='Serial')
serial_port_thread.start()
# serial_port_handler()

# Start the BLE manager:
manager = MyDeviceManager(adapter_name='hci0')
manager.start_discovery()
manager.run()
