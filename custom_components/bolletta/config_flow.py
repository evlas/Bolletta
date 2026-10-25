"""Config Flow per l'integrazione Bolletta Elettrica."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
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
        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_pun()

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Bolletta Luce"): cv.string,
                vol.Required(
                    CONF_OPERATOR, default=OPERATOR_ENGIE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=k, label=v)
                            for k, v in OPERATORS.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_POWER_KW, default=DEFAULT_POWER_KW
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_USE_MULTIORARIO, default=True
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_pun(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Secondo step: Selezione delle entità PUN da Home Assistant."""
        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_operator_params()

        multiorario = self._user_data.get(CONF_USE_MULTIORARIO, True)

        schema_dict: dict[Any, Any] = {
            vol.Optional(CONF_PUN_F0): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        }

        if multiorario:
            schema_dict.update(
                {
                    vol.Required(CONF_PUN_F1): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PUN_F2): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_PUN_F3): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                }
            )

        return self.async_show_form(
            step_id="pun",
            data_schema=vol.Schema(schema_dict),
        )

    async def async_step_operator_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Terzo step: Parametri contrattuali dell'operatore."""
        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_arera()

        operator = self._user_data.get(CONF_OPERATOR, OPERATOR_ENGIE)
        preset = OPERATOR_PRESETS.get(operator, OPERATOR_PRESETS[OPERATOR_ENGIE])

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CCL, default=preset["ccl"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PCV, default=preset["pcv"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=500.0,
                        step=0.01,
                        unit_of_measurement="€/anno",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_DISPBT, default=preset["dispbt"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-100.0,
                        max=100.0,
                        step=0.01,
                        unit_of_measurement="€/anno",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD, default=preset["pd"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD_FORFETTARIO, default=preset["pd_forfettario"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_INCLUDE_LOSSES, default=preset["include_losses"]
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_ACCISA, default=preset["accisa"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=0.5,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_IVA, default=preset["iva"]
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="operator_params",
            data_schema=data_schema,
        )

    async def async_step_arera(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Quarto step: Collegamento entità ARERA (opzionale o auto-rilevamento)."""
        if user_input is not None:
            self._user_data.update(user_input)
            title = self._user_data.get("name", f"Bolletta {self._user_data.get(CONF_OPERATOR, '')}")
            return self.async_create_entry(title=title, data=self._user_data)

        # Prova a rilevare automaticamente entità ARERA standard se presenti nel registro
        def find_arera(entity_id: str) -> str | None:
            state = self.hass.states.get(entity_id)
            return entity_id if state is not None else None

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ARERA_S1,
                    description={"suggested_value": find_arera("sensor.arera_quota_fissa")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_S2,
                    description={"suggested_value": find_arera("sensor.arera_quota_potenza")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_S3,
                    description={"suggested_value": find_arera("sensor.arera_quota_energia")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_UC3,
                    description={"suggested_value": find_arera("sensor.arera_uc3")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_UC6_QE,
                    description={"suggested_value": find_arera("sensor.arera_uc6_qe")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_UC6_QP,
                    description={"suggested_value": find_arera("sensor.arera_uc6_qp")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_ASOS,
                    description={"suggested_value": find_arera("sensor.arera_asos")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_ARERA_ARIM,
                    description={"suggested_value": find_arera("sensor.arera_arim")},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            }
        )

        return self.async_show_form(
            step_id="arera",
            data_schema=data_schema,
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
            return self.async_create_entry(title="", data=user_input)

        entry_data = {**self.config_entry.data, **self.config_entry.options}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_KW,
                    default=entry_data.get(CONF_POWER_KW, DEFAULT_POWER_KW),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CCL,
                    default=entry_data.get(CONF_CCL, 0.0152),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PCV,
                    default=entry_data.get(CONF_PCV, 69.88),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=500.0,
                        step=0.01,
                        unit_of_measurement="€/anno",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_DISPBT,
                    default=entry_data.get(CONF_DISPBT, -10.77),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-100.0,
                        max=100.0,
                        step=0.01,
                        unit_of_measurement="€/anno",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD,
                    default=entry_data.get(CONF_PD, 0.0018),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PD_FORFETTARIO,
                    default=entry_data.get(CONF_PD_FORFETTARIO, 0.0),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_INCLUDE_LOSSES,
                    default=entry_data.get(CONF_INCLUDE_LOSSES, True),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_ACCISA,
                    default=entry_data.get(CONF_ACCISA, 0.0227),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=0.5,
                        step=0.000001,
                        unit_of_measurement="€/kWh",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_IVA,
                    default=entry_data.get(CONF_IVA, 10.0),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=30.0,
                        step=0.5,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_PUN_F0,
                    description={"suggested_value": entry_data.get(CONF_PUN_F0)},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F1,
                    description={"suggested_value": entry_data.get(CONF_PUN_F1)},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F2,
                    description={"suggested_value": entry_data.get(CONF_PUN_F2)},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_PUN_F3,
                    description={"suggested_value": entry_data.get(CONF_PUN_F3)},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
