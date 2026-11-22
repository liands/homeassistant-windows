"""PartyLight effect speed."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Expose speed using the light's coordinator."""
    if discovery_info is not None:
        async_add_entities([EffectSpeed(hass.data[DOMAIN])])


class EffectSpeed(CoordinatorEntity, NumberEntity):
    """Speed level reported and accepted by the lamp."""

    _attr_name = "JBL PartyLight Velocidade"
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.address}_effect_speed"

    @property
    def native_value(self):
        data = self.coordinator.data
        return data.speed if data else None

    async def async_set_native_value(self, value):
        await self.coordinator.async_control(speed=round(value))
