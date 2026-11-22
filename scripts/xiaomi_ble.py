"""Collect Xiaomi LYWSD03MMC MiBeacon v4/v5 readings on Windows using Bleak."""

import argparse
import asyncio
from datetime import datetime, timezone
import getpass
import json
from pathlib import Path
import re
import struct
import tempfile

from bleak import BleakClient, BleakScanner
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

ROOT = Path(__file__).resolve().parents[1] / "runtime" / "xiaomi_ble"
CONFIG = ROOT / "sensors.json"
SNAPSHOT = ROOT / "latest.json"
MIBEACON = "0000fe95-0000-1000-8000-00805f9b34fb"
THERMOMETER = 0x055B
GATT_SERVICE = "ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6"
GATT_READING = "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6"


def normalize_address(value):
    address = value.replace(":", "").replace("-", "").upper()
    if not re.fullmatch(r"[0-9A-F]{12}", address):
        raise ValueError("Expected a 12-digit Bluetooth address")
    return address


def settings():
    try:
        records = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    return {
        normalize_address(address): {
            "name": config["name"],
            "key": bytes.fromhex(config["bindkey"]) if config.get("bindkey") else None,
        }
        for address, config in records.items()
    }


def save_json(path, data):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     delete=False) as file:
        temporary = Path(file.name)
        try:
            json.dump(data, file, ensure_ascii=True, indent=2)
            file.write("\n")
            file.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def enroll(address, name):
    address = normalize_address(address)
    key = getpass.getpass("Bindkey Xiaomi (32 hex; vazio se o sensor nao usa chave): ").strip()
    if key and not re.fullmatch(r"[0-9A-Fa-f]{32}", key):
        raise SystemExit("A bindkey deve ter 32 caracteres hexadecimais.")
    records = settings()
    records[address] = {"name": name, "key": bytes.fromhex(key) if key else None}
    save_json(CONFIG, {
        item: {"name": record["name"], "bindkey": record["key"].hex() if record["key"] else None}
        for item, record in records.items()
    })
    print(f"Sensor …{address[-4:]} cadastrado.")


def decode(frame, address, key):
    flags = int.from_bytes(frame[:2], "little")
    if flags & 0x80 or not flags & 0x40:
        return "no_measurement", {}
    offset = 5
    mac = bytes.fromhex(address)[::-1]
    if flags & 0x10:
        if frame[5:11] != mac:
            return "address_mismatch", {}
        offset = 11
    if flags & 0x20:
        if offset >= len(frame):
            return "invalid_frame", {}
        offset += 2 if frame[offset] & 0x20 else 1
    if flags & 0x08:
        if flags >> 12 not in (4, 5):
            return "unsupported_encryption", {}
        if key is None:
            return "bindkey_required", {}
        if len(key) != 16 or len(frame) < offset + 10:
            return "invalid_frame", {}
        nonce = mac + frame[2:5] + frame[-7:-4]
        try:
            payload = AESCCM(key, tag_length=4).decrypt(
                nonce, frame[offset:-7] + frame[-4:], b"\x11"
            )
        except InvalidTag:
            return "bindkey_mismatch", {}
    else:
        payload = frame[offset:]

    result = {}
    while len(payload) >= 3:
        metric, count = struct.unpack_from("<HB", payload)
        data = payload[3:3 + count]
        if len(data) != count:
            return "invalid_frame", {}
        if metric == 0x1004 and count == 2:
            result["temperature_c"] = struct.unpack("<h", data)[0] / 10
        elif metric == 0x1006 and count == 2:
            result["humidity_pct"] = struct.unpack("<H", data)[0] / 10
        elif metric == 0x100D and count == 4:
            temp, humidity = struct.unpack("<hH", data)
            result.update(temperature_c=temp / 10, humidity_pct=humidity / 10)
        elif metric == 0x100A and count == 1:
            result["battery_pct"] = data[0]
        payload = payload[3 + count:]
    return ("ok" if result else "no_measurement"), result


def publish(snapshot, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        previous = {}
    rooms = {}
    for address, observation in snapshot["sensors"].items():
        # Keep the most recent valid reading of each metric across missed scans.
        sample = dict(previous.get("rooms", {}).get(address, {}))
        for metric, value in observation["measurements"].items():
            sample[metric] = {"value": value, "at": snapshot["collected_at"]}
        rooms[address] = sample
    save_json(path, {"collected_at": snapshot["collected_at"], "rooms": rooms})


async def read_gatt(device):
    async with asyncio.timeout(25):
        async with BleakClient(device, services=[GATT_SERVICE], timeout=14, pair=False) as client:
            received = asyncio.get_running_loop().create_future()

            def on_value(characteristic, data):
                if len(data) == 5 and not received.done():
                    temperature, humidity, _ = struct.unpack("<hBH", data)
                    if -50 <= temperature / 100 <= 80 and 0 <= humidity <= 100:
                        received.set_result({"temperature_c": temperature / 100, "humidity_pct": humidity})

            await client.start_notify(GATT_READING, on_value)
            return await asyncio.wait_for(received, 8)


async def collect(seconds, discover, publish_path=None):
    registered = settings()
    if not discover and not registered:
        raise SystemExit("Cadastre um sensor antes de coletar.")
    observations = {}
    devices = {}

    def receive(device, advertisement):
        frame = advertisement.service_data.get(MIBEACON, b"")
        if len(frame) < 5 or int.from_bytes(frame[2:4], "little") != THERMOMETER:
            return
        address = normalize_address(device.address)
        config = registered.get(address)
        if not discover and config is None:
            return
        devices[address] = device
        observation = observations.setdefault(address, {
            "name": config["name"] if config else None, "packets": 0,
            "statuses": set(), "measurements": {},
        })
        observation["packets"] += 1
        observation["rssi_dbm"] = advertisement.rssi
        observation["version"] = frame[1] >> 4
        status, values = decode(frame, address, config["key"] if config else None)
        observation["statuses"].add(status)
        if config:
            observation["measurements"].update(values)

    async with BleakScanner(receive, scanning_mode="passive"):
        await asyncio.sleep(seconds)

    if not discover:
        for address, observation in observations.items():
            measurements = observation["measurements"]
            if "temperature_c" in measurements and "humidity_pct" in measurements:
                continue
            try:
                measurements.update(await read_gatt(devices[address]))
                observation["statuses"].add("gatt_ok")
            except TimeoutError:
                observation["statuses"].add("gatt_timeout")
            except Exception as error:
                observation["statuses"].add("gatt_" + type(error).__name__)

    for observation in observations.values():
        observation["statuses"] = sorted(observation["statuses"])
    if discover:
        print(json.dumps({
            address: {key: value for key, value in observation.items() if key != "measurements"}
            for address, observation in observations.items()
        }))
        return

    for address, config in registered.items():
        if address not in observations:
            observations[address] = {"name": config["name"], "packets": 0,
                                     "statuses": ["not_seen"], "measurements": {}}
    snapshot = {"collected_at": datetime.now(timezone.utc).isoformat(), "sensors": observations}
    save_json(SNAPSHOT, snapshot)
    if publish_path is not None:
        publish(snapshot, publish_path)
    print(json.dumps({
        address[-4:]: observation["statuses"] for address, observation in observations.items()
    }))


def self_test():
    address = "A4C138000001"
    key = bytes.fromhex("00112233445566778899aabbccddeeff")
    reading = struct.pack("<HBhH", 0x100D, 4, -25, 625)
    header = struct.pack("<HHB", 0x5048, THERMOMETER, 2)
    counter = b"\x01\x02\x03"
    nonce = bytes.fromhex(address)[::-1] + header[2:5] + counter
    ciphertext = AESCCM(key, tag_length=4).encrypt(nonce, reading, b"\x11")
    frame = header + ciphertext[:-4] + counter + ciphertext[-4:]
    assert decode(frame, address, key) == ("ok", {"temperature_c": -2.5, "humidity_pct": 62.5})
    assert decode(frame, address, None) == ("bindkey_required", {})
    assert decode(frame, address, bytes(16)) == ("bindkey_mismatch", {})
    assert decode(b"\x40" + header[1:] + reading, address, None)[0] == "ok"
    print("MiBeacon decoder self-test passed")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--seconds", type=int, default=75)
    modes = cli.add_mutually_exclusive_group()
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--enroll", nargs=2, metavar=("ADDRESS", "NAME"))
    cli.add_argument("--publish", type=Path, help="Update a measurement-only file for Home Assistant.")
    args = cli.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    if args.self_test:
        self_test()
    elif args.enroll:
        enroll(*args.enroll)
    else:
        if not 1 <= args.seconds <= 300:
            cli.error("--seconds must be between 1 and 300")
        asyncio.run(collect(args.seconds, args.discover, args.publish))


if __name__ == "__main__":
    main()
