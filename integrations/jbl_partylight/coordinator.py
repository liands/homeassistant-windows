"""Shared Bluetooth coordinator for PartyLight entities."""

from datetime import timedelta
import logging

from bleak.exc import BleakError
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


_LOGGER = logging.getLogger(__name__)


class PartyLightCoordinator(DataUpdateCoordinator):
    """Refresh state without keeping the app's Bluetooth connection occupied."""

    def __init__(self, hass, device):
        super().__init__(
            hass, _LOGGER, config_entry=None, name="JBL PartyLight Stick",
            update_interval=timedelta(seconds=90), always_update=False,
        )
        self.device = device

    async def _async_update_data(self):
        try:
            return await self.device.exchange()
        except (BleakError, OSError, RuntimeError, TimeoutError) as error:
            raise UpdateFailed(f"Falha ao consultar a PartyLight Stick: {type(error).__name__}") from error

    async def async_control(self, **options):
        try:
            state = await self.device.exchange(**options)
        except (BleakError, OSError, RuntimeError, TimeoutError) as error:
            raise HomeAssistantError(
                "A JBL não confirmou o comando. Confira se está ligada e se o app JBL está fechado."
            ) from error
        self.async_set_updated_data(state)
