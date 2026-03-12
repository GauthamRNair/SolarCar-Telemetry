"""
Raspberry Pi translation of the ESP32 battery telemetry API.

This keeps the same JSON shape as src/main.cpp and serves:
- GET /
- GET /api/battery
"""

import asyncio
import os
import threading
import time
from typing import Any, Dict, Optional

from flask import Flask, jsonify

from redodo_bms import RedodoBMS


class BatteryTelemetryService:
    def __init__(self, mac_address: str, update_interval_s: float = 2.0) -> None:
        self.mac_address = mac_address
        self.update_interval_s = update_interval_s
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_payload: Dict[str, Any] = self._empty_payload()

    def _empty_payload(self) -> Dict[str, Any]:
        return {
            "timestamp": int(time.time()),
            "mac": self.mac_address,
            "connected": False,
            "voltage": 0.0,
            "current": 0.0,
            "soc": 0,
            "soh": "0%",
            "mosfetTemp": 0,
            "cellTemp": 0,
            "remainingAh": 0.0,
            "fullCapacityAh": 0.0,
            "protectionState": "Unknown",
            "balancingState": "Unknown",
            "batteryState": "Unknown",
            "dischargeCycles": 0,
            "cellVoltages": [],
        }

    def _translate_payload(self, bms_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "timestamp": int(time.time()),
            "mac": self.mac_address,
            "connected": bool(bms_data.get("connected", False)),
            "voltage": float(bms_data.get("voltage", 0.0)),
            "current": float(bms_data.get("current", 0.0)),
            "soc": int(bms_data.get("soc", 0)),
            "soh": str(bms_data.get("soh", "0%")),
            "mosfetTemp": bms_data.get("mosfet_temp", 0),
            "cellTemp": bms_data.get("cell_temp", 0),
            "remainingAh": float(bms_data.get("remaining_ah", 0.0)),
            "fullCapacityAh": float(bms_data.get("full_capacity_ah", 0.0)),
            "protectionState": str(bms_data.get("protection_state", "Unknown")),
            "balancingState": str(bms_data.get("balancing_state", "Unknown")),
            "batteryState": str(bms_data.get("battery_state", "Unknown")),
            "dischargeCycles": int(bms_data.get("discharge_cycles", 0)),
            "cellVoltages": list(bms_data.get("cell_voltages", [])),
        }

    async def _run(self) -> None:
        bms = RedodoBMS(self.mac_address)
        try:
            while not self._stop_event.is_set():
                if not bms.data.get("connected", False):
                    connected = await bms.connect()
                    if not connected:
                        with self._lock:
                            self._latest_payload = self._empty_payload()
                        await asyncio.sleep(5)
                        continue

                updated = await bms.update()
                if updated:
                    with self._lock:
                        self._latest_payload = self._translate_payload(bms.get_data())
                else:
                    with self._lock:
                        stale = dict(self._latest_payload)
                        stale["timestamp"] = int(time.time())
                        stale["connected"] = bool(bms.data.get("connected", False))
                        self._latest_payload = stale

                await asyncio.sleep(self.update_interval_s)
        finally:
            await bms.disconnect()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        def runner() -> None:
            asyncio.run(self._run())

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest_payload)


def create_app(service: BatteryTelemetryService) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def root() -> Any:
        return jsonify(service.get_snapshot())

    @app.route("/api/battery")
    def api_battery() -> Any:
        return jsonify(service.get_snapshot())

    return app


def main() -> None:
    mac = os.getenv("REDODO_BATTERY_MAC", "C8:47:80:1C:E2:85")
    host = os.getenv("BATTERY_API_HOST", "0.0.0.0")
    port = int(os.getenv("BATTERY_API_PORT", "8000"))

    service = BatteryTelemetryService(mac_address=mac, update_interval_s=2.0)
    service.start()

    app = create_app(service)
    try:
        app.run(host=host, port=port)
    finally:
        service.stop()


if __name__ == "__main__":
    main()
