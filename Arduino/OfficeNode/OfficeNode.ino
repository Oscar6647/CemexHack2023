#include "DHT.h"
#include "config.h"
#include <Websockets.h>
#include <Servo.h>
#include <ArduinoWebsockets.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

#define DHTTYPE DHT11
#define dht_dpin 0
DHT dht(dht_dpin, DHTTYPE);

#define RED_LED 14    // D5
#define GREEN_LED 12  // D6
#define YELLOW_LED 13 // D7

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
    else if (action == "getHumidity")
    {
        wsClient.sendResponse(getHumidity(), "humidity");
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

float getTemp()
{
    return dht.readTemperature();
}

void loop()
{
    // Listen for events
    wsClient.poll();

    // Example of sending data every specific time
    if (millis() - lastTime > SEND_TIME_INTERVAL)
    {
        lastTime = millis();
        // wsClient.sendResponse(getTemp(), "temperature");
    }
}
