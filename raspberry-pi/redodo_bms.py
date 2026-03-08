"""
Redodo BMS BLE Client for Raspberry Pi
Connects to Redodo battery via Bluetooth and reads telemetry data
"""
import asyncio
import struct
from bleak import BleakClient, BleakScanner
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BLE UUIDs (update these based on actual Redodo BMS protocol)
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Query command to request battery data
QUERY_COMMAND = bytes([0xDD, 0xA5, 0x03, 0x00, 0xFF, 0xFD, 0x77])


class RedodoBMS:
    def __init__(self, mac_address: str):
        self.mac_address = mac_address
        self.client: Optional[BleakClient] = None
        self.data: Dict = {
            'connected': False,
            'voltage': 0.0,
            'current': 0.0,
            'soc': 0,
            'soh': '0%',
            'mosfet_temp': 0,
            'cell_temp': 0,
            'remaining_ah': 0.0,
            'full_capacity_ah': 0.0,
            'protection_state': 'Unknown',
            'balancing_state': 'Unknown',
            'battery_state': 'Unknown',
            'discharge_cycles': 0,
            'cell_voltages': []
        }
        self._notification_event = asyncio.Event()
        self._last_response = None

    async def connect(self) -> bool:
        """Connect to the BMS via BLE"""
        try:
            logger.info(f"Connecting to {self.mac_address}...")
            self.client = BleakClient(self.mac_address, timeout=10.0)
            await self.client.connect()
            
            if self.client.is_connected:
                logger.info("Connected to Redodo BMS")
                # Subscribe to notifications
                await self.client.start_notify(NOTIFY_UUID, self._notification_handler)
                self.data['connected'] = True
                return True
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.data['connected'] = False
            return False

    async def disconnect(self):
        """Disconnect from the BMS"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.data['connected'] = False
            logger.info("Disconnected from BMS")

    def _notification_handler(self, sender, data: bytearray):
        """Handle incoming BLE notifications"""
        self._last_response = bytes(data)
        self._notification_event.set()
        logger.debug(f"Received {len(data)} bytes: {data.hex()}")

    async def update(self):
        """Request and update battery data"""
        if not self.client or not self.client.is_connected:
            logger.warning("Not connected to BMS")
            return False

        try:
            # Clear previous response
            self._notification_event.clear()
            self._last_response = None

            # Send query command
            await self.client.write_gatt_char(WRITE_UUID, QUERY_COMMAND)
            
            # Wait for response (timeout 2 seconds)
            try:
                await asyncio.wait_for(self._notification_event.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for BMS response")
                return False

            if self._last_response:
                self._parse_response(self._last_response)
                return True
            return False

        except Exception as e:
            logger.error(f"Update failed: {e}")
            self.data['connected'] = False
            return False

    def _parse_response(self, data: bytes):
        """Parse BMS response data"""
        try:
            if len(data) < 20:
                logger.warning(f"Response too short: {len(data)} bytes")
                return

            # Parse based on Redodo BMS protocol
            # NOTE: This is a basic parser - adjust based on actual protocol
            
            # Total voltage (bytes 4-5, big-endian, x10)
            self.data['voltage'] = struct.unpack('>H', data[4:6])[0] / 100.0
            
            # Current (bytes 6-7, big-endian, signed, x10)
            self.data['current'] = struct.unpack('>h', data[6:8])[0] / 100.0
            
            # Remaining capacity (bytes 8-9, big-endian, x10)
            self.data['remaining_ah'] = struct.unpack('>H', data[8:10])[0] / 100.0
            
            # Full capacity (bytes 10-11)
            if len(data) > 11:
                self.data['full_capacity_ah'] = struct.unpack('>H', data[10:12])[0] / 100.0
            
            # SOC (byte 23)
            if len(data) > 23:
                self.data['soc'] = data[23]
            
            # Temperatures (bytes 27-30)
            if len(data) > 29:
                self.data['mosfet_temp'] = struct.unpack('>h', data[27:29])[0] / 10.0
                self.data['cell_temp'] = struct.unpack('>h', data[29:31])[0] / 10.0 if len(data) > 30 else 0
            
            # Cell voltages (if available)
            # This depends on the actual protocol structure
            # Placeholder for now
            self.data['cell_voltages'] = []
            
            # States
            self.data['protection_state'] = 'Normal'
            self.data['battery_state'] = 'Charging' if self.data['current'] > 0 else 'Discharging'
            
            logger.info(f"Updated: {self.data['voltage']:.2f}V, {self.data['current']:.2f}A, SOC: {self.data['soc']}%")
            
        except Exception as e:
            logger.error(f"Parse error: {e}")

    def get_data(self) -> Dict:
        """Get current battery data"""
        return self.data.copy()


async def scan_for_redodo_batteries(timeout: float = 5.0) -> List[str]:
    """Scan for nearby Redodo batteries"""
    logger.info("Scanning for Redodo batteries...")
    devices = await BleakScanner.discover(timeout=timeout)
    
    redodo_devices = []
    for device in devices:
        if device.name and device.name.startswith("R-"):
            logger.info(f"Found: {device.name} ({device.address})")
            redodo_devices.append(device.address)
    
    return redodo_devices


# Example usage
async def main():
    # Scan for batteries
    batteries = await scan_for_redodo_batteries()
    
    if not batteries:
        logger.error("No Redodo batteries found")
        return
    
    # Connect to first battery found (or use specific MAC)
    mac = "C8:47:80:1C:E2:85"  # Or use batteries[0]
    bms = RedodoBMS(mac)
    
    if await bms.connect():
        try:
            while True:
                await bms.update()
                data = bms.get_data()
                print(f"\nVoltage: {data['voltage']:.2f}V")
                print(f"Current: {data['current']:.2f}A")
                print(f"SOC: {data['soc']}%")
                print(f"Remaining: {data['remaining_ah']:.2f}Ah")
                await asyncio.sleep(2)
        except KeyboardInterrupt:
            logger.info("Stopping...")
        finally:
            await bms.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
