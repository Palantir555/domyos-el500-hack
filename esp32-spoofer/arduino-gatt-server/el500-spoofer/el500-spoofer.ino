/*
    Based on Neil Kolban example for IDF:
   https://github.com/nkolban/esp32-snippets/blob/master/cpp_utils/tests/BLE%20Tests/SampleServer.cpp
    Ported to Arduino ESP32 by Evandro Copercini
    updates by chegewara
*/

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/

// JC: Old UUIDs used by the example
// #define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
// #define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

// permission : properties : value
#define SERVICE_UUID_METADATA     "0000180a-0000-1000-8000-00805f9b34fb"
    #define CHARACT_UUID_META_0   "00002a29-0000-1000-8000-00805f9b34fb" // R : R : value-str="ISSC"
    #define CHARACT_UUID_META_1   "00002a24-0000-1000-8000-00805f9b34fb" // R : R : value-str="BM70"
    #define CHARACT_UUID_META_2   "00002a25-0000-1000-8000-00805f9b34fb" // R : R : value-str="0000"
    #define CHARACT_UUID_META_3   "00002a27-0000-1000-8000-00805f9b34fb" // R : R : value-str="5505 102_BLDK3"
    #define CHARACT_UUID_META_4   "00002a26-0000-1000-8000-00805f9b34fb" // R : R : value-str="009500"
    #define CHARACT_UUID_META_5   "00002a28-0000-1000-8000-00805f9b34fb" // R : R : value-str="0000"
    #define CHARACT_UUID_META_6   "00002a23-0000-1000-8000-00805f9b34fb" // R : R : value="0000000000000000"
    #define CHARACT_UUID_META_7   "00002a2a-0000-1000-8000-00805f9b34fb" // R : R : value="0000000001000000"
#define SERVICE_UUID_UNKNOWN_0    "49535343-5d82-6099-9348-7aac4d5fbc51" 
    #define CHARACT_UUID_UNK0_0   "49535343-026e-3a9b-954c-97daef17e26e" // W : W/N
#define SERVICE_UUID_UNKNOWN_1    "49535343-c9d0-cc83-a44a-6fe238d06d33" 
    #define CHARACT_UUID_UNK1_0   "49535343-aca3-481c-91ec-d85e28a60318" // W : W/N
#define SERVICE_UUID_STATEREPORTS "49535343-fe7d-4ae5-8fa9-9fafd205e455" 
    #define CHARACT_UUID_STATES   "49535343-1e4d-4bd9-ba61-23c647249616" // W : W/WnR/N
    #define CHARACT_UUID_ST_1     "49535343-8841-43f4-a8d4-ecbe34729bb3" // W : W/WnR/N
    #define CHARACT_UUID_ST_2     "49535343-4c8a-39b3-2f49-511cff073b7e" // W : W/N

void setup()
{
    Serial.begin(115200);
    Serial.println("Starting BLE work!");

    BLEDevice::init("Domyos-EL-4242");
    BLEServer* pServer = BLEDevice::createServer();
#if 0
    BLEService *pService = pServer->createService(SERVICE_UUID);
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                           CHARACTERISTIC_UUID,
                                           BLECharacteristic::PROPERTY_READ |
                                           BLECharacteristic::PROPERTY_WRITE
                                         );

    pCharacteristic->setValue("Hello World says Neil");
    pService->start();
    // BLEAdvertising *pAdvertising = pServer->getAdvertising();  // this still is working for backward compatibility
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
#else

    // service
    BLEService* pServiceMeta = pServer->createService(SERVICE_UUID_METADATA);
    BLECharacteristic* pCh0  = pServiceMeta->createCharacteristic(
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
    // service
    BLEService* pServiceUnk0 = pServer->createService(SERVICE_UUID_UNKNOWN_0);
    BLECharacteristic* pCh8  = pServiceUnk0->createCharacteristic(
        CHARACT_UUID_UNK1_0,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);
    // service
    BLEService* pServiceUnk1    = pServer->createService(SERVICE_UUID_UNKNOWN_1);
    BLECharacteristic* pCh9 = pServiceUnk0->createCharacteristic(
        CHARACT_UUID_UNK0_0,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);
    // service
    BLEService* pServiceStates = pServer->createService(SERVICE_UUID_STATEREPORTS);
    BLECharacteristic* pCh10 = pServiceUnk0->createCharacteristic(
        CHARACT_UUID_STATES, BLECharacteristic::PROPERTY_WRITE |
                                 BLECharacteristic::PROPERTY_WRITE_NR |
                                 BLECharacteristic::PROPERTY_NOTIFY);
    BLECharacteristic* pCh11 = pServiceUnk0->createCharacteristic(
        CHARACT_UUID_ST_1, BLECharacteristic::PROPERTY_WRITE |
                               BLECharacteristic::PROPERTY_WRITE_NR |
                               BLECharacteristic::PROPERTY_NOTIFY);
    BLECharacteristic* pCh12 = pServiceUnk0->createCharacteristic(
        CHARACT_UUID_ST_2,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_NOTIFY);
    pServiceMeta->start();
    pServiceUnk0->start();
    pServiceUnk1->start();
    pServiceStates->start();
#endif
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID_METADATA);
    pAdvertising->addServiceUUID(SERVICE_UUID_UNKNOWN_0);
    pAdvertising->addServiceUUID(SERVICE_UUID_UNKNOWN_1);
    pAdvertising->addServiceUUID(SERVICE_UUID_STATEREPORTS);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06); // functions that help with iPhone connections issue
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    Serial.println("Characteristic defined! Now you can read it in your phone!");
}

void loop()
{
    // put your main code here, to run repeatedly:
    delay(2000);
}
