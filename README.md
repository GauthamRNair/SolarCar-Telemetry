# Redodo Battery Telemetry API

ESP32 BLE client that connects to Redodo batteries and exposes telemetry data via HTTP JSON API.

## Features

- ✅ Connects to Redodo battery via Bluetooth Low Energy (BLE)
- ✅ Exposes JSON API endpoint with real-time battery data
- ✅ Auto-reconnect on connection loss
- ✅ Ready for ngrok/Cloudflare tunnel for global access

## Hardware

- ESP32-S3 DevKit C-1 (or compatible ESP32 with BLE)
- Redodo battery with BLE (tested with R-51100GBN250)

## Setup

### 1. Configure Credentials

Copy the example secrets file:
```bash
cp secrets.h.example secrets.h
```

Edit `secrets.h` with your WiFi and battery MAC:
```cpp
#define WIFI_SSID "your_wifi_name"
#define WIFI_PASSWORD "your_password"
#define BATTERY_MAC "C8:47:80:1C:E2:85"
```

### 2. Build and Upload

```bash
pio run --target upload
pio device monitor
```

### 3. Get API Endpoint

After WiFi connects, serial monitor will show:
```
IP Address: 192.168.1.123
API Endpoint: http://192.168.1.123/api/battery
```

## API Endpoint

**GET** `/api/battery`

Returns JSON with current battery telemetry:

```json
{
  "mac": "C8:47:80:1C:E2:85",
  "connected": true,
  "voltage": 25.6,
  "current": 2.5,
  "soc": 85,
  "soh": "100%",
  "mosfetTemp": 18,
  "cellTemp": 17,
  "remainingAh": 42.5,
  "fullCapacityAh": 50.0,
  "protectionState": "Normal",
  "balancingState": "Idle",
  "batteryState": "Discharging",
  "dischargeCycles": 12,
  "cellVoltages": [3.2, 3.21, 3.2, 3.19, 3.2, 3.21, 3.2, 3.2]
}
```

## Global Access with ngrok

Make your local API globally accessible:

```bash
ngrok http 192.168.1.123:80
```

Your endpoint becomes:
```
https://xyz123.ngrok-free.app/api/battery
```

For free alternative, see [Cloudflare Tunnel setup](NGROK_SETUP.md).

## Usage Examples

**cURL:**
```bash
curl http://192.168.1.123/api/battery
```

**JavaScript:**
```javascript
fetch('http://192.168.1.123/api/battery')
  .then(res => res.json())
  .then(data => console.log(`${data.voltage}V, ${data.soc}%`));
```

**Python:**
```python
import requests
r = requests.get('http://192.168.1.123/api/battery')
print(r.json()['voltage'])
```

## Multiple Batteries

Deploy multiple ESP32s, each with different battery MAC addresses. Each will expose its own endpoint that can be aggregated by an external dashboard.

## License

MIT
