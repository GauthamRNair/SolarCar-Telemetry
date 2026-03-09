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

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
