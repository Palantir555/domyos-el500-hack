#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <esp_system.h>
#include <BLE2902.h>

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

// JC: Old UUIDs used by the example
// #define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
// #define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

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
#if 0 // Human-readable serial report
        std::string value = pCharacteristic->getValue();
        Serial.print("Written to [");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]:");
        Serial.print("\t");
        for (int i = 0; i < value.length(); i++)
        {
            Serial.print(value.c_str()[i], HEX);
            Serial.print(" ");
        }
        Serial.println();
        {
            char serialMsg[255] = "";
            sprintf(serialMsg, "W,%s,%s\n", pCharacteristic->getUUID().toString().c_str(), value.c_str());// TODO JC highest: This is broken. value will sometimes have null characters within packets
        }
#else
        // serialize into a machine-readable format, send via Serial
        std::string value = pCharacteristic->getValue();
        Serial.print("Write[char:");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.print("][msg:");
        for (int i = 0; i < value.length(); i++)
        {
            Serial.print(value.c_str()[i], HEX);
            Serial.print(" ");
        }
        Serial.println("]");
#endif
    }

    void onRead(BLECharacteristic* pCharacteristic)
    {
        //std::string value = pCharacteristic->getValue();
        Serial.print("Read[char:");
        Serial.print(pCharacteristic->getUUID().toString().c_str());
        Serial.println("]");
        // TODO JC high: Wait for python to send back the real device's char value, parse it, and:
        // pCharacteristic->setValue(( uint8_t* )(receivedReadValue), sizeof(receivedReadValue));
        // The BLE stack will automatically return the newly set value to the BLE client
    }
};

void setup()
{
    Serial.begin(115200);
    Serial.println("Starting BLE work!");

    // uint8_t spoofed_mac[] = {0xe8, 0x5d, 0x86, 0xbf, 0x35, 0x9d}; // Original mac address - for identical cloning
    uint8_t spoofed_mac[] = {0xe8, 0x5d, 0x86, 0xbf, 0x35, 0x42}; // Original mac address - for identical cloning
    esp_base_mac_addr_set(spoofed_mac);

    BLEDevice::init("Domyos-EL-4242");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // service { characts }
    BLEService* pServiceMeta = pServer->createService(SERVICE_UUID_METADATA);
    {
        BLECharacteristic* pCh0 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_0, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh1 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_1, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh2 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_2, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh3 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_3, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh4 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_4, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh5 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_5, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh6 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_6, BLECharacteristic::PROPERTY_READ);
        BLECharacteristic* pCh7 = pServiceMeta->createCharacteristic(
            CHARACT_UUID_META_7, BLECharacteristic::PROPERTY_READ);
        pCh0->setCallbacks(new MyCharactCallbacks());
        pCh1->setCallbacks(new MyCharactCallbacks());
        pCh2->setCallbacks(new MyCharactCallbacks());
        pCh3->setCallbacks(new MyCharactCallbacks());
        pCh4->setCallbacks(new MyCharactCallbacks());
        pCh5->setCallbacks(new MyCharactCallbacks());
        pCh6->setCallbacks(new MyCharactCallbacks());
        pCh7->setCallbacks(new MyCharactCallbacks());

        // Set up readable values
        pCh0->setValue(( uint8_t* )(ch0_val), sizeof(ch0_val));
        pCh1->setValue(( uint8_t* )(ch1_val), sizeof(ch1_val));
        pCh2->setValue(( uint8_t* )(ch2_val), sizeof(ch2_val));
        pCh3->setValue(( uint8_t* )(ch3_val), sizeof(ch3_val));
        pCh4->setValue(( uint8_t* )(ch4_val), sizeof(ch4_val));
        pCh5->setValue(( uint8_t* )(ch5_val), sizeof(ch5_val));
        pCh6->setValue(( uint8_t* )(ch6_val), sizeof(ch6_val));
        pCh7->setValue(( uint8_t* )(ch7_val), sizeof(ch7_val));
    }

    // service { characts }
    BLEService* pServiceUnk0 = pServer->createService(SERVICE_UUID_UNKNOWN_0);
    {
        BLECharacteristic* pCh8 = pServiceUnk0->createCharacteristic(
            CHARACT_UUID_UNK0_0, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        pCh8->setCallbacks(new MyCharactCallbacks());
        //descrCharUnk0.setNotifications(1);
        pCh8->addDescriptor(&descrCharUnk0);
    }

    // service { characts }
    BLEService* pServiceUnk1    = pServer->createService(SERVICE_UUID_UNKNOWN_1);
    {
        BLECharacteristic* pCh9 = pServiceUnk1->createCharacteristic(
            CHARACT_UUID_UNK1_0, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        pCh9->setCallbacks(new MyCharactCallbacks());
        //descrCharUnk1.setNotifications(1);
        pCh9->addDescriptor(&descrCharUnk1);
    }

    // service { characts }
    BLEService* pServiceStates = pServer->createService(SERVICE_UUID_STATEREPORTS);
    {
        BLECharacteristic* pCh10 = pServiceStates->createCharacteristic(
            CHARACT_UUID_STATES, BLECharacteristic::PROPERTY_WRITE |
                                     BLECharacteristic::PROPERTY_WRITE_NR |
                                     BLECharacteristic::PROPERTY_NOTIFY);
        BLECharacteristic* pCh11 = pServiceStates->createCharacteristic(
            CHARACT_UUID_ST_1, BLECharacteristic::PROPERTY_WRITE |
                                   BLECharacteristic::PROPERTY_WRITE_NR |
                                   BLECharacteristic::PROPERTY_NOTIFY);
        BLECharacteristic* pCh12 = pServiceStates->createCharacteristic(
            CHARACT_UUID_ST_2, BLECharacteristic::PROPERTY_WRITE |
                                   BLECharacteristic::PROPERTY_NOTIFY);
        pCh10->setCallbacks(new MyCharactCallbacks());
        descrCharStateStates.setNotifications(1);
        pCh10->addDescriptor(&descrCharStateStates);
        pCh11->setCallbacks(new MyCharactCallbacks());
        pCh12->setCallbacks(new MyCharactCallbacks());
        //descrCharStateSt2.setNotifications(1);
        pCh12->addDescriptor(&descrCharStateSt2);
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
    Serial.println("Characteristics defined!");
}

void loop()
{
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
