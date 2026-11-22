"""Expose JBL PartyLight Stick as a Home Assistant light."""

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_EFFECT, ATTR_RGB_COLOR, ColorMode, LightEntity, LightEntityFeature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .protocol import EFFECTS

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the light and keep it listed when temporarily unreachable."""
    if discovery_info is None:
        return
    coordinator = hass.data[DOMAIN]
    async_add_entities([PartyLightEntity(coordinator, coordinator.device.address)])


class PartyLightEntity(CoordinatorEntity, LightEntity):
    """RGB light with PartyLight Stick effects."""

    _attr_name = "JBL PartyLight Stick"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, coordinator, address):
        super().__init__(coordinator)
        self._attr_unique_id = address

    @property
    def is_on(self):
        return self.coordinator.data.pattern != 0 if self.coordinator.data else None

    @property
    def rgb_color(self):
        return self.coordinator.data.rgb if self.coordinator.data else None

    @property
    def brightness(self):
        state = self.coordinator.data
        if state is None or state.intensity is None:
            return None
        return round(state.intensity * 255 / 100)

    @property
    def effect(self):
        return EFFECTS.get(self.coordinator.data.pattern) if self.coordinator.data else None

    @property
    def effect_list(self):
        return [EFFECTS[code] for code in self.coordinator.data.effects if code in EFFECTS] if self.coordinator.data else []

    async def async_turn_on(self, **kwargs):
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        intensity = max(1, round(brightness * 100 / 255)) if brightness is not None else None
        effect = kwargs.get(ATTR_EFFECT)
        if effect is not None and effect not in self.effect_list:
            raise HomeAssistantError(f"Efeito não disponível na luminária: {effect}")
        pattern = next((code for code, name in EFFECTS.items() if name == effect), None)
        await self.coordinator.async_control(
            on=True, pattern=pattern, rgb=kwargs.get(ATTR_RGB_COLOR), intensity=intensity
        )

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_control(on=False)
