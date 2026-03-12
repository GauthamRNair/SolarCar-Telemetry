# Redodo Battery Telemetry API

## Overview

This project implements a Bluetooth Low Energy (BLE) client for the ESP32 microcontroller platform. It connects to Redodo lithium iron phosphate (LiFePO4) batteries and reads real-time telemetry data. The telemetry logic resides in the `src/` directory.

## Features

- BLE connectivity to Redodo battery management systems
- Real-time battery telemetry acquisition
- Automatic reconnection upon connection loss

## Hardware Requirements

| Component | Specification |
|---|---|
| Microcontroller | ESP32-S3 DevKit C-1 (or any ESP32 variant with BLE support) |
| Battery | Redodo battery with BLE capability (validated with model R-51100GBN250) |

## Installation and Configuration

### Step 1: Configure Credentials

Create the secrets header file by copying the provided template:

**Unix/macOS:**
```bash
cp src/secrets.h.example src/secrets.h
```

**Windows (PowerShell):**
```powershell
Copy-Item src\secrets.h.example src\secrets.h
```

Open `src/secrets.h` and populate the following fields with the appropriate values:

```cpp
#define WIFI_SSID "your_wifi_name"
#define WIFI_PASSWORD "your_password"

// Will not be the same between batteries
#define BATTERY_MAC "C8:47:80:1C:E2:85" 
```

### Step 2: Build and Upload Firmware

Compile the firmware and flash it to the ESP32, then open the serial monitor to verify operation:

```bash
pio run --target upload
pio device monitor
```



## Multi-Battery Deployment

This system supports monitoring multiple batteries simultaneously. Each battery requires a dedicated ESP32 configured with the corresponding BLE MAC address.

## Raspberry Pi Setup (Python Translation)

The `raspberry-pi/` folder contains a Python translation of the battery telemetry API.

### What It Provides

- BLE polling of the Redodo battery using `bleak`
- Same JSON payload shape as the ESP32 API
- HTTP endpoints:
	- `GET /`
	- `GET /api/battery`

### Raspberry Pi Prerequisites

Install these on Raspberry Pi OS (Bookworm/Bullseye):

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv bluetooth bluez libbluetooth-dev
```

Notes:
- `bluez` and `bluetooth` are required for BLE access from Python.
- You may need to enable Bluetooth in `raspi-config` on some images.

### Python Environment and Dependencies

From the repository root:

```bash
cd raspberry-pi
python3 -m venv .venv
source .venv/bin/activate

# Fix SSL/certificate issues on Pi before installing packages
sudo apt install -y ca-certificates
pip install --upgrade pip setuptools

pip install -r requirements.txt
```

### Configure Battery MAC (Required)

Set your battery MAC before running:

```bash
export REDODO_BATTERY_MAC="C8:47:80:1C:E2:85"
```

Optional API bind values (defaults shown):

```bash
export BATTERY_API_HOST="0.0.0.0"
export BATTERY_API_PORT="8000"
```

### Run the Pi API

```bash
cd raspberry-pi
source .venv/bin/activate
python battery_telemetry_api.py
```

Test locally:

```bash
curl http://127.0.0.1:8000/api/battery
```

### Optional: Expose API with cloudflared

Install cloudflared:

```bash
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```

If your Pi is 32-bit ARM, use the armhf package instead:

```bash
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-armhf.deb
sudo dpkg -i cloudflared-linux-armhf.deb
```

Start a quick tunnel to the local API:

```bash
cloudflared tunnel --url http://localhost:8000
```

Cloudflared will print a public HTTPS URL forwarding to your Pi API.

### Optional: Run on Boot (systemd)

Create `/etc/systemd/system/battery-telemetry.service`:

```ini
[Unit]
Description=Battery Telemetry API (Raspberry Pi)
After=network.target bluetooth.target

[Service]
Type=simple
WorkingDirectory=/home/pi/SolarCar-Telemetry/raspberry-pi
Environment=REDODO_BATTERY_MAC=C8:47:80:1C:E2:85
Environment=BATTERY_API_HOST=0.0.0.0
Environment=BATTERY_API_PORT=8000
ExecStart=/home/pi/SolarCar-Telemetry/raspberry-pi/.venv/bin/python battery_telemetry_api.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable battery-telemetry.service
sudo systemctl start battery-telemetry.service
sudo systemctl status battery-telemetry.service
```

### Troubleshooting (Pi)

- BLE permission issues:
	- Ensure Bluetooth service is running: `sudo systemctl status bluetooth`
	- Try restarting it: `sudo systemctl restart bluetooth`
- No battery found:
	- Confirm battery is powered and in BLE range.
	- Confirm `REDODO_BATTERY_MAC` is correct.
- Flask import error:
	- Ensure venv is active and `pip install -r requirements.txt` completed.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
