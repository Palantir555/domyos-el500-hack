#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <esp_system.h>
#include <BLE2902.h>

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

// permission : properties : value
#define SERVICE_UUID_METADATA     "0000180a-0000-1000-8000-00805f9b34fb"
    #define CHARACT_UUID_META_0   "00002a29-0000-1000-8000-00805f9b34fb" // R : R : value-str="ISSC"
        constexpr char ch0_val[] = "ISSC";
    #define CHARACT_UUID_META_1   "00002a24-0000-1000-8000-00805f9b34fb" // R : R : value-str="BM70"
        constexpr char ch1_val[] = "BM70";
    #define CHARACT_UUID_META_2   "00002a25-0000-1000-8000-00805f9b34fb" // R : R : value-str="0000"
        constexpr char ch2_val[] = "0000";
    #define CHARACT_UUID_META_3   "00002a27-0000-1000-8000-00805f9b34fb" // R : R : value-str="5505 102_BLDK3"
        constexpr char ch3_val[] = "5505 102_BLDK3";
    #define CHARACT_UUID_META_4   "00002a26-0000-1000-8000-00805f9b34fb" // R : R : value-str="009500"
        constexpr char ch4_val[] = "009500";
    #define CHARACT_UUID_META_5   "00002a28-0000-1000-8000-00805f9b34fb" // R : R : value-str="0000"
        constexpr char ch5_val[] = "0000";
    #define CHARACT_UUID_META_6   "00002a23-0000-1000-8000-00805f9b34fb" // R : R : value="0000000000000000"
        constexpr uint8_t ch6_val[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
    #define CHARACT_UUID_META_7   "00002a2a-0000-1000-8000-00805f9b34fb" // R : R : value="0000000001000000"
        constexpr uint8_t ch7_val[] = {0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00};
#define SERVICE_UUID_UNKNOWN_0    "49535343-5d82-6099-9348-7aac4d5fbc51" 
    #define CHARACT_UUID_UNK0_0   "49535343-026e-3a9b-954c-97daef17e26e" // W : W/N
        BLE2902 descrCharUnk0;
#define SERVICE_UUID_UNKNOWN_1    "49535343-c9d0-cc83-a44a-6fe238d06d33" 
    #define CHARACT_UUID_UNK1_0   "49535343-aca3-481c-91ec-d85e28a60318" // W : W/N
        BLE2902 descrCharUnk1;
#define SERVICE_UUID_STATEREPORTS "49535343-fe7d-4ae5-8fa9-9fafd205e455" 
    #define CHARACT_UUID_STATES   "49535343-1e4d-4bd9-ba61-23c647249616" // W : W/WnR/N
        BLE2902 descrCharStateStates;
    #define CHARACT_UUID_ST_1     "49535343-8841-43f4-a8d4-ecbe34729bb3" // W : W/WnR/N
    #define CHARACT_UUID_ST_2     "49535343-4c8a-39b3-2f49-511cff073b7e" // W : W/N
        BLE2902 descrCharStateSt2;

#define NUM_CHARACTERISTICS 13
BLECharacteristic* characts_array[NUM_CHARACTERISTICS];

BLEServer* pServer      = NULL;
bool deviceConnected    = false;
bool oldDeviceConnected = false;


class MyServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer* serv)
    {
        deviceConnected = true;
        Serial.println("connect cback");
    };

    void onMTUChanged(BLEServer* pServer, uint16_t mtu)
    {
        Serial.print("MTU Changed to: ");
        Serial.println(mtu);
    }

    void onDisconnect(BLEServer* serv)
    {
        deviceConnected = false;
        Serial.println("disconnect cback");
    }
};


class MyCharactCallbacks : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic* pCharacteristic)
    {
        // serialize into a machine-readable format, send via Serial
        std::string value = pCharacteristic->getValue();
        Serial.print("Write[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][");
        for (int i = 0; i < value.length(); i++)
        {
            // Print the byte as a hex value (always two digits)
            Serial.printf("%02x ", value.c_str()[i]);
        }
        Serial.println("]");
    }

    void onWriteRequest(BLECharacteristic* pCharacteristic, const uint8_t* data, size_t len, bool isNotify)
    {
        // serialize into a machine-readable format, send via Serial
        Serial.print("WriteReq[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][");
        for (int i = 0; i < len; i++)
        {
            // Print the byte as a hex value (always two digits)
            Serial.printf("%02x ", data[i]);
        }
        Serial.println("]");
    }

    void onWriteWithoutResponse(BLECharacteristic* pCharacteristic)
    {
        std::string value = pCharacteristic->getValue();
        Serial.print("WriteWithoutResponse[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][");
        for (int i = 0; i < value.length(); i++)
        {
            // Print the byte as a hex value (always two digits)
            Serial.printf("%02x ", value.c_str()[i]);
        }
        Serial.println("]");
    }

    void onRead(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        Serial.print("Read[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
        // TODO JC high: Wait for python to send back the real device's char value, parse it, and:
        // pCharacteristic->setValue(( uint8_t* )(receivedReadValue), sizeof(receivedReadValue));
        // The BLE stack will automatically return the newly set value to the BLE client
    }

    void onReadRequest(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        Serial.print("ReadReq[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
        // TODO JC high: Wait for python to send back the real device's char value, parse it, and:
        // pCharacteristic->setValue(( uint8_t* )(receivedReadValue), sizeof(receivedReadValue));
        // The BLE stack will automatically return the newly set value to the BLE client
    }

    void onNotify(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        #if 0 // This is getting the notifications sent by ourselves, cluttering the output
        Serial.print("Notify[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][");
        std::string value = pCharacteristic->getValue();
        for (int i = 0; i < value.length(); i++)
        {
            // Print the byte as a hex value (always two digits)
        Serial.print("Notify[");
            Serial.printf("%02x ", value.c_str()[i]);
        }
        Serial.println("]");
        #endif
    }

    #if 0
    void onStatus(BLECharacteristic* pCharacteristic, Status s, uint32_t code)
    {
        // Says copilot (TODO verify):
        // This callback is invoked when the status of the characteristic changes
        // (e.g. when the characteristic is notified/indicated).
        // Within BLE, the status represents the state of the client's CCCD (Client Characteristic Configuration Descriptor)
        Serial.print("Status[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][status:");
        Serial.print(s);
        Serial.print("][code:");
        Serial.print(code);
        Serial.println("]");
    }
    #endif

    void onIndicate(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        Serial.print("Indicate[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
    }

    void onUnsubscribe(BLECharacteristic* pCharacteristic)
    {
        Serial.print("Unsubscribe[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
    }

    void onConfirm(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        Serial.print("Confirm[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
    }

    void onAuthentication(BLECharacteristic* pCharacteristic, bool isEncryptedRead, bool isEncryptedWrite, bool isSignedWrite)
    {
        Serial.print("Authentication[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][isEncryptedRead:");
        Serial.print(isEncryptedRead);
        Serial.print("][isEncryptedWrite:");
        Serial.print(isEncryptedWrite);
        Serial.print("][isSignedWrite:");
        Serial.print(isSignedWrite);
        Serial.println("]");
    }

    void onSecurityResponse(BLECharacteristic* pCharacteristic, Status s, uint32_t code)
    {
        Serial.print("SecurityResponse[");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][status:");
        Serial.print(s);
        Serial.print("][code:");
        Serial.print(code);
        Serial.println("]");
    }
};

void setup()
{
    Serial.begin(230400); // 115200);
    Serial.println("Starting BLE work");

    // uint8_t spoofed_mac[] = {0xe8, 0x5d, 0x86, 0xbf, 0x35, 0x9d}; // Original mac address - for identical cloning
    uint8_t spoofed_mac[] = {0xe8, 0x5d, 0x86, 0xbf, 0x35, 0x42}; // Custom mac address - for vendor mac spoofing
    esp_base_mac_addr_set(spoofed_mac);

    BLEDevice::init("Domyos-EL-4242");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // service { characts }
    BLEService* pServiceMeta = pServer->createService(SERVICE_UUID_METADATA);
    {
        characts_array[0] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_0, BLECharacteristic::PROPERTY_READ);
        characts_array[1] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_1, BLECharacteristic::PROPERTY_READ);
        characts_array[2] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_2, BLECharacteristic::PROPERTY_READ);
        characts_array[3] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_3, BLECharacteristic::PROPERTY_READ);
        characts_array[4] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_4, BLECharacteristic::PROPERTY_READ);
        characts_array[5] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_5, BLECharacteristic::PROPERTY_READ);
        characts_array[6] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_6, BLECharacteristic::PROPERTY_READ);
        characts_array[7] = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_7, BLECharacteristic::PROPERTY_READ);

        // Set up readable values
        characts_array[0]->setValue(( uint8_t* )(ch0_val), sizeof(ch0_val));
        characts_array[1]->setValue(( uint8_t* )(ch1_val), sizeof(ch1_val));
        characts_array[2]->setValue(( uint8_t* )(ch2_val), sizeof(ch2_val));
        characts_array[3]->setValue(( uint8_t* )(ch3_val), sizeof(ch3_val));
        characts_array[4]->setValue(( uint8_t* )(ch4_val), sizeof(ch4_val));
        characts_array[5]->setValue(( uint8_t* )(ch5_val), sizeof(ch5_val));
        characts_array[6]->setValue(( uint8_t* )(ch6_val), sizeof(ch6_val));
        characts_array[7]->setValue(( uint8_t* )(ch7_val), sizeof(ch7_val));
    }

    // service { characts }
    BLEService* pServiceUnk0 = pServer->createService(SERVICE_UUID_UNKNOWN_0);
    {
        characts_array[8] = pServiceUnk0->createCharacteristic(
            CHARACT_UUID_UNK0_0, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        //descrCharUnk0.setNotifications(1);
        characts_array[8]->addDescriptor(&descrCharUnk0);
    }

    // service { characts }
    BLEService* pServiceUnk1    = pServer->createService(SERVICE_UUID_UNKNOWN_1);
    {
        characts_array[9] = pServiceUnk1->createCharacteristic(
            CHARACT_UUID_UNK1_0, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        //descrCharUnk1.setNotifications(1);
        characts_array[9]->addDescriptor(&descrCharUnk1);
    }

    // service { characts }
    BLEService* pServiceStates = pServer->createService(SERVICE_UUID_STATEREPORTS);
    {
        characts_array[10] = pServiceStates->createCharacteristic(
            CHARACT_UUID_STATES, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_WRITE_NR |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        characts_array[11] = pServiceStates->createCharacteristic(
            CHARACT_UUID_ST_1, BLECharacteristic::PROPERTY_WRITE |
                                   BLECharacteristic::PROPERTY_WRITE_NR |
                                   BLECharacteristic::PROPERTY_NOTIFY);
        characts_array[12] = pServiceStates->createCharacteristic(
            CHARACT_UUID_ST_2, BLECharacteristic::PROPERTY_WRITE |
                                   BLECharacteristic::PROPERTY_NOTIFY);
        descrCharStateStates.setNotifications(1);
        characts_array[10]->addDescriptor(&descrCharStateStates);
        //descrCharStateSt2.setNotifications(1);
        characts_array[12]->addDescriptor(&descrCharStateSt2);
    }

    for(auto& ch : characts_array) {
        ch->setCallbacks(new MyCharactCallbacks());
    }

    // start services
    pServiceMeta->start();
    pServiceUnk0->start();
    pServiceUnk1->start();
    pServiceStates->start();

    // Set up advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID_METADATA);
    //pAdvertising->addServiceUUID(SERVICE_UUID_UNKNOWN_0);
    //pAdvertising->addServiceUUID(SERVICE_UUID_UNKNOWN_1);
    //pAdvertising->addServiceUUID(SERVICE_UUID_STATEREPORTS);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06); // functions that help with iPhone connections issue
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    Serial.println("Characteristics defined");
}

void read_serial_input_line()
{
    if (Serial.available())
    {
        String input_line = Serial.readStringUntil('\n');
        // Copy input_line to input_line_copy
        String input_line_copy = input_line;
        input_line.trim(); // Remove whitespace and newlines
        // Parse input_line into (command, uuid, value) according to this
        // format:
        //  "<command>,<characteristic>,<msg>\r\n"
        //  where <msg> is a byte array in hex format.
        // Example:
        // b'ReadResponse,49535343-8841-43f4-a8d4-ecbe34729bb3,F0C9B9\r\n'
        String command = input_line.substring(0, input_line.indexOf(','));
        input_line.remove(0, input_line.indexOf(',') + 1);
        String uuid = input_line.substring(0, input_line.indexOf(','));
        input_line.remove(0, input_line.indexOf(',') + 1);
        String value_hex = input_line;
        // Convert hex string to byte array. Example hex string: "F0C9B9"
        uint8_t payload[128];
        int payload_len = value_hex.length() / 2;
        assert(payload_len <= 128);
        for (int i = 0; i < payload_len; i++)
        {
            payload[i] = ( uint8_t )strtol(
                value_hex.substring(i * 2, i * 2 + 2).c_str(), NULL, 16);
        }

        if (command == "Restart")
        {
            Serial.println("Restarting ESP32...");
            ESP.restart();
        }
        else if (command == "Notify")
        { // TODO highest: might be buggy, and that's why the app sessions
          // aren't behaving?
            for (auto& c : characts_array)
            {
                if (c->getUUID().equals(BLEUUID(uuid.c_str())))
                {
                    c->setValue(payload, payload_len);
                    c->notify();
                    // Serial.println("App notified");
                    break;
                }
            }
        }
        else
        {
            // TODO high: Hitting this error SOMETIMES. Why? Is Serial dropping
            //            characters? Is the issue in the python script? Logs:
            // 'Received unrecognized serial message:'
            // '    Command: 23c647249616'
            // '    UUID: f0bcffff0000000000000000000001000100000000ff000000ab'
            // '    Value: f0bcffff0000000000000000000001000100000000ff000000ab'
            Serial.print("Received unrecognized serial message:");
            Serial.println(input_line_copy);
            Serial.println("    Command: " + command);
            Serial.println("    UUID: " + uuid);
            Serial.println("    Value: " + value_hex);
        }
    }
}

void loop()
{
    read_serial_input_line(); // To be expanded to fetch read responses. Will have to be moved elsewhere
    if (deviceConnected)
    {
        delay(1000);
    }
    else
    {
        delay(1000);
    }

    /* disconnecting */
    if (!deviceConnected && oldDeviceConnected)
    {
        delay(500); /* give the BT stack the chance to get things ready */
        pServer->startAdvertising(); /* restart advertising */
        Serial.println("start advertising");
        oldDeviceConnected = deviceConnected;
    }

    /* connecting */
    if (deviceConnected && !oldDeviceConnected)
    {
        /* do stuff here on connecting */
        oldDeviceConnected = deviceConnected;
    }
}
