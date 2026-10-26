"""Piattaforma switch per Bolletta (servizio idrico: fognatura e depurazione)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMMODITY_WATER,
    CONF_COMMODITY,
    CONF_USA_DEPURAZIONE,
    CONF_USA_FOGNATURA,
    CONF_USA_FOGNATURA_DEPURAZIONE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura gli switch per l'istanza Bolletta."""
    commodity = entry.data.get(CONF_COMMODITY)
    if commodity != COMMODITY_WATER:
        return

    contract_name = entry.data.get("name", "Bolletta Acqua")
    operator_name = entry.data.get("operator", "Acea").capitalize()

    switches = [
        BollettaWaterSwitch(
            hass=hass,
            entry=entry,
            key=CONF_USA_FOGNATURA,
            translation_key="fognatura",
            default_name="Fognatura",
            icon="mdi:pipe",
            contract_name=contract_name,
            operator_name=operator_name,
        ),
        BollettaWaterSwitch(
            hass=hass,
            entry=entry,
            key=CONF_USA_DEPURAZIONE,
            translation_key="depurazione",
            default_name="Depurazione",
            icon="mdi:waves-cleansing",
            contract_name=contract_name,
            operator_name=operator_name,
        ),
    ]

    async_add_entities(switches)


class BollettaWaterSwitch(SwitchEntity):
    """Switch per abilitare o disabilitare fognatura o depurazione nel calcolo bolletta acqua."""

    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        translation_key: str,
        default_name: str,
        icon: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza lo switch."""
        self.hass = hass
        self.entry = entry
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_name = default_name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"

        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        version = entry_data.get("version") if isinstance(entry_data, dict) else None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=contract_name,
            manufacturer=operator_name,
            model="Contratto Servizio Idrico",
            sw_version=str(version) if version else "1.0.0",
        )

    @property
    def suggested_object_id(self) -> str | None:
        """Suggerisce l'ID entità generico."""
        return self._attr_translation_key

    @property
    def is_on(self) -> bool:
        """Restituisce True se la componente tariffaria è inclusa nel calcolo."""
        opts = self.entry.options
        data = self.entry.data

        if self._key in opts:
            return bool(opts[self._key])
        if self._key in data:
            return bool(data[self._key])

        # Fallback alla vecchia chiave combinata usa_fognatura_depurazione se presente
        if CONF_USA_FOGNATURA_DEPURAZIONE in opts:
            return bool(opts[CONF_USA_FOGNATURA_DEPURAZIONE])
        if CONF_USA_FOGNATURA_DEPURAZIONE in data:
            return bool(data[CONF_USA_FOGNATURA_DEPURAZIONE])

        return True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Abilita la componente nel calcolo della bolletta."""
        new_options = dict(self.entry.options)
        new_options[self._key] = True
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disabilita la componente nel calcolo della bolletta."""
        new_options = dict(self.entry.options)
        new_options[self._key] = False
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
