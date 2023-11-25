#include "DHT.h"
#include "config.h"
#include <Websockets.h>
#include <Servo.h>
#include <ArduinoWebsockets.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <MFRC522.h>

// Define pins temperature sensor
#define DHTTYPE DHT11
#define dht_dpin 0
DHT dht(dht_dpin, DHTTYPE);

// Define pins RFID
#define RST_PIN D3
#define SS_PIN D4

MFRC522 reader(SS_PIN, RST_PIN);

const int DELAY_RFID_LECTURE = 5000;
long long int lastReadRFID = 0;

// Time to send general data to server
const long int SEND_TIME_INTERVAL = 30000;
unsigned long int lastTime = 0;

float upperBound = 24.60;
float lowerBound = 18.0;

using namespace websockets;
Websockets wsClient(config::websockets_connection_string);

// Execute when recieving a message
void onMessageCallback(WebsocketsMessage message)
{
    // Serial.print("Got Message: ");
    // Serial.println(message.data());

    DynamicJsonDocument doc(1024);
    DeserializationError err = deserializeJson(doc, message.data());

    // Check error
    if (err)
    {
        Serial.print(F("deserializeJson() failed with code "));
        Serial.println(err.c_str());
        Serial.println("Aborted action");
        return;
    }
    else
    {
        // Print message
        serializeJson(doc, Serial);
        Serial.println();
    }

    String action = doc["action"].as<String>();

    Serial.print("Action: ");
    Serial.println(action);

    if (action == "")
    {
        Serial.println("Error: no action was detected.");
        Serial.println("Aborted action");
    }
    else if (action == "getTemperature")
    {
        wsClient.sendResponse(getTemp(), "temperature");
    }
    else if (action == "getLight")
    {
        wsClient.sendResponse(getLight(), "light");
    }
    else
    {
        Serial.print("Warning: the recieved action has no implementation: ");
        Serial.println(action);
    }
}

void setup()
{
    Serial.begin(config::serialBaud);

    while (!Serial)
    {
    }

    delay(2000);
    Serial.println("Serial communication initialized.");

    dht.begin();
    Serial.println("Humidity and temperature sensor initialized.");

    SPI.begin();
    reader.PCD_Init(); // Initialize MFRC522
    Serial.println("RFID initialized");

    // Connect to wifi
    WiFi.begin(config::ssid, config::password);

    // Wait until device is connected
    while (WiFi.status() != WL_CONNECTED)
    {
        Serial.print("Wifi not connected. Status: ");
        Serial.println(WiFi.status());
        delay(500);
    }

    Serial.println("Wifi has been connected");

    // run callback when messages are received
    wsClient.onMessage(onMessageCallback);
    wsClient.initialize("generalNode", "office1-mx");

    // Send a ping
    wsClient.ping();

    Serial.println("Setup has been finished");
}

float getHumidity()
{
    return dht.readHumidity();
}

// TODO: implement
float getTemp()
{
    return 1;
    // return dht.readTemperature();
}

// TODO: implement
float getLight()
{
    return 1;
}

// Send rfid lectures to server.
void checkRFID()
{
    // Check RFID lectures
    if (!reader.PICC_IsNewCardPresent())
    {
        return;
    }

    // Check if lecture was successful, else exit loop
    if (!reader.PICC_ReadCardSerial())
    {
        return;
    }

    // If a RFID lecture has been detected recently, skip detection.
    if (millis() - lastReadRFID < DELAY_RFID_LECTURE)
    {
        return;
    }

    lastReadRFID = millis();

    Serial.println("RFID readed card successfuly");

    String reading = "";
    for (int x = 0; x < reader.uid.size; x++)
    {
        // If it is less than 10, we add zero
        if (reader.uid.uidByte[x] < 0x10)
        {
            reading += "0";
        }
        // Convert lecture from byte to hexadecimal
        reading += String(reader.uid.uidByte[x], HEX);

        // Separate bytes with dashes.
        if (x + 1 != reader.uid.size)
        {
            reading += "-";
        }
    }
    // Make string uppercase (for formatting)
    reading.toUpperCase();

    // Send lecture to server
    wsClient.sendResponse(reading, "RFID");
}

void loop()
{
    // Listen for events
    wsClient.poll();

    // Example of sending data every specific time
    if (millis() - lastTime > SEND_TIME_INTERVAL)
    {
        lastTime = millis();
        wsClient.sendResponse(getLight(), "light");
        wsClient.sendResponse(getTemp(), "temperature");
        wsClient.sendResponse("TEST-ID", "RFID");
    }

    checkRFID();
}
