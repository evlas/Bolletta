"""Config Flow per l'integrazione Bolletta Elettrica."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ACCISA,
    CONF_ARERA_ARIM,
    CONF_ARERA_ASOS,
    CONF_ARERA_S1,
    CONF_ARERA_S2,
    CONF_ARERA_S3,
    CONF_ARERA_UC3,
    CONF_ARERA_UC6_QE,
    CONF_ARERA_UC6_QP,
    CONF_CCL,
    CONF_DISPBT,
    CONF_INCLUDE_LOSSES,
    CONF_IVA,
    CONF_OPERATOR,
    CONF_PCV,
    CONF_PD,
    CONF_PD_FORFETTARIO,
    CONF_POWER_KW,
    CONF_PUN_F0,
    CONF_PUN_F1,
    CONF_PUN_F2,
    CONF_PUN_F3,
    CONF_USE_MULTIORARIO,
    DEFAULT_POWER_KW,
    DOMAIN,
    OPERATOR_ENGIE,
    OPERATOR_PRESETS,
    OPERATORS,
    POWER_PRESETS,
)

_LOGGER = logging.getLogger(__name__)


class BollettaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestione del Config Flow per Bolletta."""

    VERSION = 1

    def __init__(self) -> None:
        """Inizializza il config flow."""
        self._user_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Primo step: Nome, Operatore, Potenza impegnata e Fasce orarie."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_pun()

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Bolletta Luce"): cv.string,
                vol.Required(
                    CONF_OPERATOR, default=OPERATOR_ENGIE
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=k, label=v)
                            for k, v in OPERATORS.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_POWER_KW, default=DEFAULT_POWER_KW
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="kW",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_USE_MULTIORARIO, default=True
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_pun(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Secondo step: Selezione delle entità PUN da Home Assistant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Pulisce i valori vuoti o None
                clean_input = {k: v for k, v in user_input.items() if v}
                self._user_data.update(clean_input)
                return await self.async_step_operator_params()
            except Exception as err:
                _LOGGER.exception("Errore durante il salvataggio dei PUN: %s", err)
                errors["base"] = "unknown"

        multiorario = self._user_data.get(CONF_USE_MULTIORARIO, True)

        schema_dict: dict[Any, Any] = {}

        if multiorario:
            schema_dict.update(
                {
                    vol.Required(CONF_PUN_F1): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PUN_F2): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PUN_F3): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                }
            )
        else:
            schema_dict.update(
                {
                    vol.Required(CONF_PUN_F0): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                }
            )

        return self.async_show_form(
            step_id="pun",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_operator_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Terzo step: Parametri contrattuali dell'operatore."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                clean_input = {k: v for k, v in user_input.items() if v is not None}
                self._user_data.update(clean_input)
                return await self.async_step_arera()
            except Exception as err:
                _LOGGER.exception("Errore nei parametri operatore: %s", err)
                errors["base"] = "unknown"

        operator = self._user_data.get(CONF_OPERATOR, OPERATOR_ENGIE)
        preset = OPERATOR_PRESETS.get(operator, OPERATOR_PRESETS[OPERATOR_ENGIE])

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CCL, default=float(preset["ccl"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PCV, default=float(preset["pcv"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=1000.0,
                        step="any",
                        unit_of_measurement="€/anno",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_DISPBT, default=float(preset["dispbt"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=-200.0,
                        max=200.0,
                        step="any",
                        unit_of_measurement="€/anno",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD, default=float(preset["pd"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD_FORFETTARIO, default=float(preset["pd_forfettario"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_INCLUDE_LOSSES, default=bool(preset["include_losses"])
                ): bool,
                vol.Required(
                    CONF_ACCISA, default=float(preset["accisa"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_IVA, default=float(preset["iva"])
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=50.0,
                        step="any",
                        unit_of_measurement="%",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="operator_params",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_arera(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Quarto step: Collegamento entità ARERA (opzionale o auto-rilevamento)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v}
            self._user_data.update(clean_input)
            title = self._user_data.get("name", f"Bolletta {self._user_data.get(CONF_OPERATOR, '')}")
            return self.async_create_entry(title=title, data=self._user_data)

        # Rileva automaticamente entità ARERA standard se presenti nel registro
        schema_dict: dict[Any, Any] = {}
        arera_pairs = [
            (CONF_ARERA_S1, "sensor.arera_quota_fissa"),
            (CONF_ARERA_S2, "sensor.arera_quota_potenza"),
            (CONF_ARERA_S3, "sensor.arera_quota_energia"),
            (CONF_ARERA_UC3, "sensor.arera_uc3"),
            (CONF_ARERA_UC6_QE, "sensor.arera_uc6_qe"),
            (CONF_ARERA_UC6_QP, "sensor.arera_uc6_qp"),
            (CONF_ARERA_ASOS, "sensor.arera_asos"),
            (CONF_ARERA_ARIM, "sensor.arera_arim"),
        ]

        for conf_key, entity_id in arera_pairs:
            state = self.hass.states.get(entity_id)
            if state is not None:
                schema_dict[
                    vol.Optional(conf_key, description={"suggested_value": entity_id})
                ] = EntitySelector(EntitySelectorConfig(domain="sensor"))
            else:
                schema_dict[vol.Optional(conf_key)] = EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                )

        return self.async_show_form(
            step_id="arera",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Restituisce il gestore delle opzioni."""
        return BollettaOptionsFlowHandler(config_entry)


class BollettaOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestione dell'Options Flow per Bolletta."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inizializza."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gestisce le opzioni modificabili."""
        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v is not None}
            return self.async_create_entry(title="", data=clean_input)

        entry_data = {**self.config_entry.data, **self.config_entry.options}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_KW,
                    default=entry_data.get(CONF_POWER_KW, DEFAULT_POWER_KW),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="kW",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CCL,
                    default=float(entry_data.get(CONF_CCL, 0.0152)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PCV,
                    default=float(entry_data.get(CONF_PCV, 69.88)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=1000.0,
                        step="any",
                        unit_of_measurement="€/anno",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_DISPBT,
                    default=float(entry_data.get(CONF_DISPBT, -10.77)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=-200.0,
                        max=200.0,
                        step="any",
                        unit_of_measurement="€/anno",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD,
                    default=float(entry_data.get(CONF_PD, 0.0018)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD_FORFETTARIO,
                    default=float(entry_data.get(CONF_PD_FORFETTARIO, 0.0)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_INCLUDE_LOSSES,
                    default=bool(entry_data.get(CONF_INCLUDE_LOSSES, True)),
                ): bool,
                vol.Required(
                    CONF_ACCISA,
                    default=float(entry_data.get(CONF_ACCISA, 0.0227)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step="any",
                        unit_of_measurement="€/kWh",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_IVA,
                    default=float(entry_data.get(CONF_IVA, 10.0)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=50.0,
                        step="any",
                        unit_of_measurement="%",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_PUN_F0,
                    description={"suggested_value": entry_data.get(CONF_PUN_F0)},
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F1,
                    description={"suggested_value": entry_data.get(CONF_PUN_F1)},
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F2,
                    description={"suggested_value": entry_data.get(CONF_PUN_F2)},
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F3,
                    description={"suggested_value": entry_data.get(CONF_PUN_F3)},
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
