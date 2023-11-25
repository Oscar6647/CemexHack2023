#ifndef CONFIG_H
#define CONFIG_H

namespace config
{
    static const int serialBaud = 115200;
    // Enter server adress
    static const char *websockets_connection_string = "wss://ppcdr19jaa.execute-api.us-east-1.amazonaws.com/development/";

    const char *ssid = "";     // Enter SSID
    const char *password = ""; // Enter Password

};

#endif
