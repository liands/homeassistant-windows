"""Short-lived BLE sessions for the JBL PartyLight Stick.

Framing and UUID reference:
https://github.com/BaggaBruh/jbl-partybox-ha/blob/main/PROTOCOL.md
"""

import asyncio
from contextlib import AsyncExitStack
from dataclasses import dataclass

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

SERVICE = "65786365-6c70-6f69-6e74-2e636f6d0000"
RX = "65786365-6c70-6f69-6e74-2e636f6d0001"
TX = "65786365-6c70-6f69-6e74-2e636f6d0002"
INTENSITY = 0x45
SPEED = 0x46
EFFECTS = {2: "Neon", 8: "Personalizado", 9: "Loop", 10: "Bounce", 11: "Trim", 12: "Switch", 13: "Freeze"}


@dataclass(frozen=True)
class LightState:
    pattern: int
    rgb: tuple[int, int, int]
    effects: tuple[int, ...]
    intensity: int | None
    speed: int | None


def percent_field(fields, code):
    value = fields.get(code, b"")
    return value[0] if len(value) == 1 and value[0] <= 100 else None


def device_fields(reply):
    if not reply or reply[0] != 0:
        raise RuntimeError("Resposta da JBL inesperada")
    fields = {}
    offset = 1
    while offset + 2 <= len(reply):
        key, length = reply[offset:offset + 2]
        offset += 2
        fields[key] = reply[offset:offset + length]
        offset += length
    if offset != len(reply):
        raise RuntimeError("Resposta da JBL incompleta")
    return fields


class LightConnection:
    """Decode complete notification frames and wait for each command response."""

    def __init__(self, client):
        self.client = client
        self.buffer = bytearray()
        self.messages = asyncio.Queue()

    def notification(self, characteristic, payload):
        self.buffer.extend(payload)
        while self.buffer:
            if self.buffer[0] != 0xAA:
                del self.buffer[0]
                continue
            if len(self.buffer) < 3:
                return
            end = 3 + self.buffer[2]
            if len(self.buffer) < end:
                return
            self.messages.put_nowait((self.buffer[1], bytes(self.buffer[3:end])))
            del self.buffer[:end]

    async def command(self, code, payload=b"", expected=0):
        while not self.messages.empty():
            self.messages.get_nowait()
        async with asyncio.timeout(4):
            await self.client.write_gatt_char(TX, bytes((0xAA, code, len(payload))) + payload, response=True)
            while True:
                reply, body = await self.messages.get()
                if reply == 0 and len(body) >= 2 and body[0] == code:
                    if body[1]:
                        raise RuntimeError("A JBL recusou o comando")
                    if expected == 0:
                        return body
                elif reply == expected and reply != 0:
                    return body

    async def state(self):
        tokens = device_fields(await self.command(0x31, expected=0x32))
        if len(tokens.get(0x31, ())) != 1 or len(tokens.get(0x32, ())) != 3:
            raise RuntimeError("Resposta de luz incompleta")
        return LightState(
            tokens[0x31][0], tuple(tokens[0x32]), tuple(tokens.get(0x4A, ())),
            percent_field(tokens, INTENSITY), percent_field(tokens, SPEED),
        )

    async def serial(self):
        fields = device_fields(await self.command(0x11, expected=0x12))
        return fields.get(0x40, b"").decode("ascii", errors="replace").strip("\x00 ").upper()

    async def pattern(self, value):
        await self.command(0x33, bytes((0, 0x31, 1, value)))

    async def rgb(self, value):
        await self.command(0x33, bytes((0, 0x36, 1, 1, 0x32, 3, *value)))

    async def intensity(self, value):
        await self.command(0x33, bytes((0, INTENSITY, 1, value)))

    async def speed(self, value):
        await self.command(0x33, bytes((0, SPEED, 1, value)))


class PartyLight:
    """Query the lamp over the existing adapter for each operation."""

    def __init__(self, address, serial=None):
        self.address = address
        self.serial = serial.strip().upper() if serial else None
        self._current_address = address
        self.lock = asyncio.Lock()
        self.last_pattern = None

    async def _connect_device(self, stack, device):
        """Read the serial before making the connection available for control."""
        for use_cached in (True, False):
            try:
                async with AsyncExitStack() as candidate:
                    client = await candidate.enter_async_context(
                        BleakClient(device, timeout=12, services=[SERVICE],
                                    winrt={"use_cached_services": use_cached})
                    )
                    link = LightConnection(client)
                    await client.start_notify(RX, link.notification)
                    if self.serial and await link.serial() != self.serial:
                        return None
                    stack.push_async_callback(candidate.pop_all().aclose)
                    return link
            except (BleakError, OSError, RuntimeError, TimeoutError):
                continue
        return None

    async def _connect(self, stack):
        known = await BleakScanner.find_device_by_address(
            self._current_address, timeout=3 if self.serial else 8
        )
        if known is not None:
            link = await self._connect_device(stack, known)
            if link is not None:
                return link
        if not self.serial:
            raise TimeoutError("PartyLight fora de alcance")

        seen = await BleakScanner.discover(timeout=12, return_adv=True)
        candidates = sorted(seen.values(), key=lambda pair: pair[1].rssi, reverse=True)
        for device, advert in candidates:
            if known is not None and device.address.upper() == known.address.upper():
                continue
            name = advert.local_name or device.name or ""
            if device.address.upper() != self._current_address and "partylight stick" not in name.casefold():
                continue
            link = await self._connect_device(stack, device)
            if link is not None:
                self._current_address = device.address.upper()
                return link
        raise TimeoutError("PartyLight com o número de série configurado não encontrada")

    async def exchange(self, *, on=None, pattern=None, rgb=None, intensity=None, speed=None):
        async with self.lock, asyncio.timeout(54), AsyncExitStack() as stack:
            link = await self._connect(stack)
            state = await link.state()
            if state.pattern:
                self.last_pattern = state.pattern
            if on is None and speed is None:
                return state

            expected_pattern = state.pattern
            if on:
                if pattern is None and rgb is not None and 8 in state.effects:
                    pattern = 8
                if pattern is None:
                    pattern = state.pattern or self.last_pattern or next(iter(state.effects), 2)
                if state.pattern != pattern:
                    await link.pattern(pattern)
                expected_pattern = pattern
                if rgb is not None:
                    await link.rgb(rgb)
                if intensity is not None and (
                    state.intensity != intensity or state.pattern != pattern or rgb is not None
                ):
                    await link.intensity(intensity)
            elif on is False:
                if state.pattern:
                    await link.pattern(0)
                expected_pattern = 0

            if speed is not None and state.speed != speed:
                await link.speed(speed)

            confirmed = await link.state()
            if (
                confirmed.pattern != expected_pattern
                or (rgb is not None and confirmed.rgb != tuple(rgb))
                or (intensity is not None and confirmed.intensity != intensity)
                or (speed is not None and confirmed.speed != speed)
            ):
                raise RuntimeError("O estado consultado não confirmou o comando")
            if confirmed.pattern:
                self.last_pattern = confirmed.pattern
            return confirmed
