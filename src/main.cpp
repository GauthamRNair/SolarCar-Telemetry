#include <Arduino.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <BMSClient.h>
#include <secrets.h>

BMSClient bmsClient;
AsyncWebServer server(80);
unsigned long lastUpdateMs = 0;

String getBatteryJSON() {
    String json = "{";
    json += "\"mac\":\"" + String(BATTERY_MAC) + "\",";
    json += "\"connected\":" + String(bmsClient.isConnected() ? "true" : "false") + ",";
    json += "\"voltage\":" + String(bmsClient.getTotalVoltage(), 2) + ",";
    json += "\"current\":" + String(bmsClient.getCurrent(), 2) + ",";
    json += "\"soc\":" + String(bmsClient.getSOC()) + ",";
    json += "\"soh\":\"" + bmsClient.getSOH() + "\",";
    json += "\"mosfetTemp\":" + String(bmsClient.getMosfetTemp()) + ",";
    json += "\"cellTemp\":" + String(bmsClient.getCellTemp()) + ",";
    json += "\"remainingAh\":" + String(bmsClient.getRemainingAh(), 2) + ",";
    json += "\"fullCapacityAh\":" + String(bmsClient.getFullCapacityAh(), 2) + ",";
    json += "\"protectionState\":\"" + bmsClient.getProtectionState() + "\",";
    json += "\"balancingState\":\"" + bmsClient.getBalancingState() + "\",";
    json += "\"batteryState\":\"" + bmsClient.getBatteryState() + "\",";
    json += "\"dischargeCycles\":" + String(bmsClient.getDischargesCount()) + ",";
    
    std::vector<float> cells = bmsClient.getCellVoltages();
    json += "\"cellVoltages\":[";
    for (size_t i = 0; i < cells.size(); i++) {
        json += String(cells[i], 3);
        if (i < cells.size() - 1) json += ",";
    }
    json += "]";
    json += "}";
    return json;
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    Serial.println("Starting Redodo Battery API...");

    // Connect to WiFi
    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("API Endpoint: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/api/battery");
    
    // Setup API server
    server.on("/api/battery", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send(200, "application/json; charset=UTF-8", getBatteryJSON());
    });
    server.begin();
    Serial.println("API server started\n");
    
    // Connect to battery
    Serial.print("Connecting to battery ");
    Serial.println(BATTERY_MAC);
    bmsClient.init(BATTERY_MAC);
    if (bmsClient.connect()) {
        Serial.println("Battery connected\n");
    } else {
        Serial.println("Battery connection failed - will retry\n");
    }
}

void loop() {
    // Auto-reconnect if disconnected
    if (!bmsClient.isConnected()) {
        Serial.println("Reconnecting to battery...");
        if (bmsClient.connect()) {
            Serial.println("Reconnected!");
        }
        delay(5000);
        return;
    }

    // Update battery data every 2 seconds
    unsigned long now = millis();
    if (now - lastUpdateMs >= 2000) {
        bmsClient.update();
        lastUpdateMs = now;
        Serial.printf("Updated: %.2fV, %.2fA, %d%%\n", 
            bmsClient.getTotalVoltage(), 
            bmsClient.getCurrent(), 
            bmsClient.getSOC());
    }

    delay(100);
}