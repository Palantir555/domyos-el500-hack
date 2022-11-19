# Sniffing BLE comms using ubertooth one and wireshark

1. Install Wireshark and follow the ubertooth's setup docs
2. `mkfifo /tmp/pipe`
2. `ubertooth-btle -f -c /tmp/pipe`
3. Wireshark -> Capture -> Manage Interfaces -> Local Pipes -> New -> `/tmp/pipe` -> OK -> Start
4. Find our target device
5. Set target in firmware: `ubertooth-btle -t aa:bb:cc:dd:ee:ff`
    - and/or keep capturing all traffic and filter it in wireshark:
      `btle.slave_bd_addr == e8:5d:86:bf:35:9d || btle.master_bd_addr == E8:5D:86:BF:35:9D`
6. When done, unset firmware filter with `ubertooth-btls -t none


useful display filters:

- Only connection requests and non-zero data packets:
    `btle.data_header.length > 0 || btle.advertising_header.pdu_type == 0x05`
- Only attribute read responses, write requests, and notifications:
    `btatt.opcode in { 0x0b 0x12 0x1b }`

# Connecting to the device over bluetooth

Note: The raspberry pi running this is called "eliptica", and so is its bluetooth interface name. Our target is `Domyos-EL-1919`

``
$ bluetoothctl
# scan on
[...]
[NEW] Device E8:5D:86:BF:35:9D Domyos-EL-1919
[...]
# scan off
# connect E8:5D:86:BF:35:9D
[Domyos-EL-1919]# list
Controller DC:A6:32:5A:55:99 eliptica [default]
[Domyos-EL-1919]# pair
Attempting to pair with E8:5D:86:BF:35:9D
[CHG] Device E8:5D:86:BF:35:9D Paired: yes
Pairing successful
[Domyos-EL-1919]# list
Controller DC:A6:32:5A:55:99 eliptica [default]
[Domyos-EL-1919]# list default
Too many arguments
[Domyos-EL-1919]# list eliptica
Too many arguments
[Domyos-EL-1919]# menu
Missing name argument
[Domyos-EL-1919]# menu eliptica
Unable find menu with name: eliptica
[Domyos-EL-1919]# gatt
Invalid command in menu main: gatt

Use "help" for a list of available commands in a menu.
Use "menu <submenu>" if you want to enter any submenu.
Use "back" if you want to return to menu main.
[Domyos-EL-1919]# scan
Missing on/off argument
[Domyos-EL-1919]# list
Controller DC:A6:32:5A:55:99 eliptica [default]
[Domyos-EL-1919]# show
Controller DC:A6:32:5A:55:99 (public)
        Name: eliptica
        Alias: eliptica
        Class: 0x002c0000
        Powered: yes
        Discoverable: no
        DiscoverableTimeout: 0x000000b4
        Pairable: yes
        UUID: A/V Remote Control        (0000110e-0000-1000-8000-00805f9b34fb)
        UUID: Audio Source              (0000110a-0000-1000-8000-00805f9b34fb)
        UUID: PnP Information           (00001200-0000-1000-8000-00805f9b34fb)
        UUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)
        UUID: Headset                   (00001108-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control Target (0000110c-0000-1000-8000-00805f9b34fb)
        UUID: Generic Access Profile    (00001800-0000-1000-8000-00805f9b34fb)
        UUID: Generic Attribute Profile (00001801-0000-1000-8000-00805f9b34fb)
        UUID: Device Information        (0000180a-0000-1000-8000-00805f9b34fb)
        UUID: Headset AG                (00001112-0000-1000-8000-00805f9b34fb)
        Modalias: usb:v1D6Bp0246d0537
        Discovering: no
        Roles: central
        Roles: peripheral
Advertising Features:
        ActiveInstances: 0x00 (0)
        SupportedInstances: 0x05 (5)
        SupportedIncludes: tx-power
        SupportedIncludes: appearance
        SupportedIncludes: local-name
``

