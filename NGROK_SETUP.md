# Global Access Setup with ngrok

## Step 1: Configure WiFi

Edit `src/main.cpp` and update these lines with your WiFi credentials:

```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

## Step 2: Upload to ESP32

```bash
pio run --target upload
pio device monitor
```

Wait for the serial output to show:
```
WiFi connected! IP: 192.168.x.x
Web server started
```

Note the IP address shown.

## Step 3: Test Locally

Open a browser and go to:
```
http://192.168.x.x
```

You should see the battery dashboard with live telemetry data.

## Step 4: Install ngrok

### Windows
Download from: https://ngrok.com/download

Or with Chocolatey:
```powershell
choco install ngrok
```

### Sign up (free)
1. Create account at https://ngrok.com/
2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

## Step 5: Create Global Tunnel

In a new terminal/PowerShell window:

```bash
ngrok http 192.168.x.x:80
```

Replace `192.168.x.x` with your ESP32's IP from Step 2.

You'll see output like:
```
Forwarding   https://abcd-1234-5678.ngrok-free.app -> http://192.168.x.x:80
```

## Step 6: Access Globally

Share the ngrok URL (e.g., `https://abcd-1234-5678.ngrok-free.app`) with anyone.

They can access your battery dashboard from anywhere in the world!

## API Endpoints

### Dashboard (HTML)
```
GET /
```

### JSON API
```
GET /api/battery
```

Returns:
```json
{
  "mac": "C8:47:80:1C:E2:85",
  "connected": true,
  "voltage": 25.6,
  "current": 2.5,
  "soc": 85,
  "soh": "100%",
  "mosfetTemp": 25,
  "cellTemp": 24,
  "remainingAh": 42.5,
  "fullCapacityAh": 50.0,
  "protectionState": "Normal",
  "balancingState": "Idle",
  "batteryState": "Discharging",
  "dischargeCycles": 12,
  "cellVoltages": [3.2, 3.21, 3.2, 3.19, 3.2, 3.21, 3.2, 3.2]
}
```

## Tips

- **Free ngrok**: URL changes each time you restart ngrok
- **Paid ngrok**: Get a static domain
- **Security**: ngrok URLs are public but hard to guess
- **Keep PC running**: ngrok must stay running for tunnel to work
- **Auto-refresh**: Dashboard updates every 2 seconds automatically

## Troubleshooting

### ESP32 can't connect to WiFi
- Check SSID/password are correct
- Ensure 2.4GHz WiFi (ESP32-S3 doesn't support 5GHz)

### ngrok can't reach ESP32
- Ensure PC and ESP32 are on same network
- Check firewall isn't blocking port 80
- Verify ESP32 IP with `pio device monitor`

### Dashboard shows "Disconnected"
- Battery may be off or out of BLE range
- Check serial monitor for connection errors
