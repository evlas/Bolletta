"""Config Flow per l'integrazione Bolletta (Energia Elettrica, Acqua, Gas)."""
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
    COMMODITIES,
    COMMODITY_ENERGY,
    COMMODITY_GAS,
    COMMODITY_WATER,
    CONF_ACCISA,
    CONF_ARERA_ARIM,
    CONF_ARERA_ASOS,
    CONF_ARERA_DISPBT,
    CONF_ARERA_S1,
    CONF_ARERA_S2,
    CONF_ARERA_S3,
    CONF_ARERA_UC3,
    CONF_ARERA_UC6_QE,
    CONF_ARERA_UC6_QP,
    CONF_CCL,
    CONF_COMMODITY,
    CONF_FORMULA_ENERGIA,
    CONF_FORMULA_QUOTA_FISSA,
    CONF_INCLUDE_LOSSES,
    CONF_IVA,
    CONF_OFFER,
    CONF_OPERATOR,
    CONF_PCV,
    CONF_PD,
    CONF_PD_FORFETTARIO,
    CONF_POWER_KW,
    CONF_PUN_F0,
    CONF_PUN_F1,
    CONF_PUN_F2,
    CONF_PUN_F3,
    CONF_QF_DEPURAZIONE,
    CONF_QF_FOGNATURA,
    CONF_QF_IDRICO,
    CONF_S1,
    CONF_S2,
    CONF_S3,
    CONF_S4,
    CONF_T_AGEVOLATA,
    CONF_T_BASE,
    CONF_T_DEPURAZIONE,
    CONF_T_ECC1,
    CONF_T_ECC2,
    CONF_T_ECC3,
    CONF_T_FOGNATURA,
    CONF_UI1,
    CONF_UI2,
    CONF_UI3,
    CONF_USA_DEPURAZIONE,
    CONF_USA_FOGNATURA,
    CONF_USA_FOGNATURA_DEPURAZIONE,
    CONF_USE_MULTIORARIO,
    CONF_WATER_ANNUAL_BASELINE,
    CONF_WATER_SENSOR,
    DEFAULT_FORMULA_ENERGIA,
    DEFAULT_FORMULA_QUOTA_FISSA,
    DEFAULT_POWER_KW,
    DEFAULT_WATER_VALUES,
    DOMAIN,
    FALLBACK_ARERA,
)
from .operators_loader import load_operators_and_offers

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
        """Primo step: Selezione del tipo di utenza (Energia Elettrica, Acqua, Gas)."""
        if user_input is not None:
            commodity = user_input.get(CONF_COMMODITY, COMMODITY_ENERGY)
            self._user_data[CONF_COMMODITY] = commodity

            if commodity == COMMODITY_WATER:
                return await self.async_step_water_init()
            if commodity == COMMODITY_GAS:
                return await self.async_step_gas_init()
            return await self.async_step_energy_init()

        commodity_options = [
            SelectOptionDict(value=COMMODITY_ENERGY, label="⚡ Energia Elettrica (Luce)"),
            SelectOptionDict(value=COMMODITY_WATER, label="💧 Acqua (Servizio Idrico)"),
            SelectOptionDict(value=COMMODITY_GAS, label="🔥 Gas Naturale"),
        ]

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_COMMODITY, default=COMMODITY_ENERGY
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=commodity_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    # =========================================================================
    # FLUSSO ENERGIA ELETTRICA
    # =========================================================================
    async def async_step_energy_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configurazione base fornitura energia elettrica."""
        errors: dict[str, str] = {}
        operators = load_operators_and_offers(COMMODITY_ENERGY)
        operator_options = [
            SelectOptionDict(value=op_id, label=op_data["name"])
            for op_id, op_data in operators.items()
        ]
        if not operator_options:
            operator_options = [SelectOptionDict(value="custom", label="Personalizzato")]

        default_op = "engie" if "engie" in operators else operator_options[0]["value"]

        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_offer()

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Bolletta Luce"): cv.string,
                vol.Required(
                    CONF_OPERATOR, default=default_op
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=operator_options,
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
            step_id="energy_init",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_offer(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Selezione dell'offerta specifica dell'operatore energetico."""
        errors: dict[str, str] = {}
        operators = load_operators_and_offers(COMMODITY_ENERGY)
        op_id = self._user_data.get(CONF_OPERATOR, "custom")
        op_data = operators.get(op_id, {})
        offers = op_data.get("offers", {})

        offer_options = [
            SelectOptionDict(
                value=off_id,
                label=f"{off['name']}" + (f" ({off['description']})" if off.get("description") else ""),
            )
            for off_id, off in offers.items()
        ]

        if not offer_options:
            offer_options = [SelectOptionDict(value="default", label="Offerta Standard")]

        default_offer = offer_options[0]["value"]

        if user_input is not None:
            chosen_offer_id = user_input.get(CONF_OFFER, default_offer)
            self._user_data[CONF_OFFER] = chosen_offer_id

            chosen_offer = offers.get(chosen_offer_id, {})
            for key, val in chosen_offer.items():
                if key not in ("dispbt", "name", "id", "description"):
                    self._user_data[key] = val
            self._user_data["offer_name"] = chosen_offer.get("name", chosen_offer_id)

            return await self.async_step_pun()

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_OFFER, default=default_offer
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=offer_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="offer",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"operator": op_data.get("name", op_id.capitalize())},
        )

    async def async_step_pun(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Selezione delle entità PUN da Home Assistant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
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
        """Personalizzazione dei parametri contrattuali dell'offerta scelta."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_arera()

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_CCL,
                    default=float(self._user_data.get(CONF_CCL, 0.0152)),
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
                    default=float(self._user_data.get(CONF_PCV, 69.88)),
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
                    CONF_PD,
                    default=float(self._user_data.get(CONF_PD, 0.0018)),
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
                    default=float(self._user_data.get(CONF_PD_FORFETTARIO, 0.0)),
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
                    default=bool(self._user_data.get(CONF_INCLUDE_LOSSES, True)),
                ): bool,
                vol.Required(
                    CONF_ACCISA,
                    default=float(self._user_data.get(CONF_ACCISA, 0.0227)),
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
                    default=float(self._user_data.get(CONF_IVA, 10.0)),
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
        """Collegamento facoltativo dei sensori ARERA."""
        errors: dict[str, str] = {}

        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v}
            self._user_data.update(clean_input)
            title = self._user_data.get("name", "Bolletta Luce")
            return self.async_create_entry(title=title, data=self._user_data)

        def _find_sensor(suffix: str) -> str | None:
            expected = f"sensor.arera_{suffix}"
            if self.hass.states.get(expected) is not None:
                return expected
            for state in self.hass.states.async_all():
                if "arera" in state.entity_id and suffix in state.entity_id:
                    return state.entity_id
            return None

        schema_dict: dict[Any, Any] = {
            vol.Optional(
                CONF_ARERA_S1, description={"suggested_value": _find_sensor("quota_fissa")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_S2, description={"suggested_value": _find_sensor("quota_potenza")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_S3, description={"suggested_value": _find_sensor("quota_energia")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_UC3, description={"suggested_value": _find_sensor("uc3")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_UC6_QE, description={"suggested_value": _find_sensor("uc6_qe")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_UC6_QP, description={"suggested_value": _find_sensor("uc6_qp")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_ASOS, description={"suggested_value": _find_sensor("asos")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_ARIM, description={"suggested_value": _find_sensor("arim")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_ARERA_DISPBT, description={"suggested_value": _find_sensor("dispbt")}
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
        }

        return self.async_show_form(
            step_id="arera",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    # =========================================================================
    # FLUSSO ACQUA (SERVIZIO IDRICO)
    # =========================================================================
    async def async_step_water_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configurazione iniziale per la bolletta dell'acqua."""
        errors: dict[str, str] = {}
        operators = load_operators_and_offers(COMMODITY_WATER)
        operator_options = [
            SelectOptionDict(value=op_id, label=op_data["name"])
            for op_id, op_data in operators.items()
        ]
        if not operator_options:
            operator_options = [SelectOptionDict(value="custom_water", label="Gestore Idrico Personalizzato")]

        default_op = "acea" if "acea" in operators else operator_options[0]["value"]

        if user_input is not None:
            self._user_data.update(user_input)
            return await self.async_step_water_offer()

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Bolletta Acqua"): cv.string,
                vol.Required(
                    CONF_OPERATOR, default=default_op
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=operator_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_WATER_SENSOR): EntitySelector(
                    EntitySelectorConfig(domain=["sensor", "input_number"])
                ),
            }
        )

        return self.async_show_form(
            step_id="water_init",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_water_offer(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Selezione della tariffa idrica dell'operatore."""
        errors: dict[str, str] = {}
        operators = load_operators_and_offers(COMMODITY_WATER)
        op_id = self._user_data.get(CONF_OPERATOR, "custom_water")
        op_data = operators.get(op_id, {})
        offers = op_data.get("offers", {})

        offer_options = [
            SelectOptionDict(
                value=off_id,
                label=f"{off['name']}" + (f" ({off['description']})" if off.get("description") else ""),
            )
            for off_id, off in offers.items()
        ]

        if not offer_options:
            offer_options = [SelectOptionDict(value="default", label="Tariffa Base")]

        default_offer = offer_options[0]["value"]

        if user_input is not None:
            chosen_offer_id = user_input.get(CONF_OFFER, default_offer)
            self._user_data[CONF_OFFER] = chosen_offer_id

            chosen_offer = offers.get(chosen_offer_id, {})
            for key, val in chosen_offer.items():
                if key not in ("name", "id", "description"):
                    self._user_data[key] = val
            self._user_data["offer_name"] = chosen_offer.get("name", chosen_offer_id)

            return await self.async_step_water_params()

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_OFFER, default=default_offer
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=offer_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="water_offer",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"operator": op_data.get("name", op_id.capitalize())},
        )

    async def async_step_water_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Parametri delle quote fisse, scaglioni e tariffe al m³ dell'acqua."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._user_data.update(user_input)
            title = self._user_data.get("name", "Bolletta Acqua")
            return self.async_create_entry(title=title, data=self._user_data)

        defaults = {**DEFAULT_WATER_VALUES, **self._user_data}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_QF_IDRICO, default=float(defaults.get(CONF_QF_IDRICO, 33.60))
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=500.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_QF_FOGNATURA, default=float(defaults.get(CONF_QF_FOGNATURA, 4.90))
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=200.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_QF_DEPURAZIONE, default=float(defaults.get(CONF_QF_DEPURAZIONE, 14.70))
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=200.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_USA_FOGNATURA,
                    default=bool(defaults.get(CONF_USA_FOGNATURA, defaults.get(CONF_USA_FOGNATURA_DEPURAZIONE, True))),
                ): bool,
                vol.Required(
                    CONF_USA_DEPURAZIONE,
                    default=bool(defaults.get(CONF_USA_DEPURAZIONE, defaults.get(CONF_USA_FOGNATURA_DEPURAZIONE, True))),
                ): bool,
                vol.Optional(
                    CONF_WATER_ANNUAL_BASELINE,
                    default=float(defaults.get(CONF_WATER_ANNUAL_BASELINE, 0.0)),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=100000.0, step="any", unit_of_measurement="m³", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_S1, default=float(defaults.get(CONF_S1, 55.0))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=500.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S2, default=float(defaults.get(CONF_S2, 108.0))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S3, default=float(defaults.get(CONF_S3, 162.0))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S4, default=float(defaults.get(CONF_S4, 216.0))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_AGEVOLATA, default=float(defaults.get(CONF_T_AGEVOLATA, 0.4445))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_BASE, default=float(defaults.get(CONF_T_BASE, 1.2583))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC1, default=float(defaults.get(CONF_T_ECC1, 1.8874))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC2, default=float(defaults.get(CONF_T_ECC2, 2.5166))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=15.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC3, default=float(defaults.get(CONF_T_ECC3, 3.7748))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=20.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_FOGNATURA, default=float(defaults.get(CONF_T_FOGNATURA, 0.3525))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=5.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_DEPURAZIONE, default=float(defaults.get(CONF_T_DEPURAZIONE, 0.7049))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=5.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI1, default=float(defaults.get(CONF_UI1, 0.004))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI2, default=float(defaults.get(CONF_UI2, 0.009))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI3, default=float(defaults.get(CONF_UI3, 0.005))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_IVA, default=float(defaults.get(CONF_IVA, 10.0))
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=50.0, step="any", unit_of_measurement="%", mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="water_params",
            data_schema=data_schema,
            errors=errors,
        )

    # =========================================================================
    # FLUSSO GAS NATURALE (PREDISPOSIZIONE)
    # =========================================================================
    async def async_step_gas_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configurazione iniziale per la fornitura di gas naturale."""
        errors: dict[str, str] = {}
        operators = load_operators_and_offers(COMMODITY_GAS)
        operator_options = [
            SelectOptionDict(value=op_id, label=op_data["name"])
            for op_id, op_data in operators.items()
        ]
        if not operator_options:
            operator_options = [SelectOptionDict(value="custom_gas", label="Fornitore Gas Personalizzato")]

        default_op = operator_options[0]["value"]

        if user_input is not None:
            self._user_data.update(user_input)
            title = self._user_data.get("name", "Bolletta Gas")
            return self.async_create_entry(title=title, data=self._user_data)

        data_schema = vol.Schema(
            {
                vol.Required("name", default="Bolletta Gas"): cv.string,
                vol.Required(
                    CONF_OPERATOR, default=default_op
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=operator_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("qf_anno", default=96.0): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=500.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX)
                ),
                vol.Required("spread", default=0.05): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=2.0, step="any", unit_of_measurement="€/Smc", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_IVA, default=10.0): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=50.0, step="any", unit_of_measurement="%", mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="gas_init",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BollettaOptionsFlowHandler:
        """Restituisce il gestore delle opzioni."""
        return BollettaOptionsFlowHandler(config_entry)


def _safe_float(val: Any, default: float) -> float:
    """Converte un valore in float gestendo None o eccezioni."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_bool(val: Any, default: bool) -> bool:
    """Converte un valore in bool gestendo None."""
    if val is None:
        return default
    return bool(val)


class BollettaOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestione delle opzioni (Options Flow) per Bolletta."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        """Inizializza evitando l'assegnazione diretta a self.config_entry (read-only su HA recente)."""
        self._config_entry_compat = config_entry
        self._options_data: dict[str, Any] = {}

    @property
    def config_entry(self) -> config_entries.ConfigEntry:
        """Restituisce il config entry in modo compatibile sia con vecchie che con nuove versioni di HA."""
        try:
            entry = super().config_entry
            if entry is not None:
                return entry
        except Exception:
            pass
        return self._config_entry_compat

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menu principale opzioni con scelta tra modifica parametri e cambio operatore."""
        self._options_data = {}
        return self.async_show_menu(
            step_id="init",
            menu_options=["params", "change_operator"],
        )

    async def async_step_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Indirizza alla schermata parametri appropriata in base alla commodity."""
        commodity = self.config_entry.data.get(CONF_COMMODITY, COMMODITY_ENERGY)
        if commodity == COMMODITY_WATER:
            return await self.async_step_water_options(user_input)
        if commodity == COMMODITY_GAS:
            return await self.async_step_gas_options(user_input)
        return await self.async_step_energy_options(user_input)

    async def async_step_change_operator(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Seleziona un nuovo operatore limitatamente alla commodity corrente."""
        commodity = self.config_entry.data.get(CONF_COMMODITY, COMMODITY_ENERGY)
        operators = load_operators_and_offers(commodity)

        operator_options = [
            SelectOptionDict(value=op_id, label=op_data.get("name", op_id.capitalize()))
            for op_id, op_data in operators.items()
        ]
        if not operator_options:
            default_label = "Personalizzato" if commodity != COMMODITY_WATER else "Gestore Personalizzato"
            operator_options = [SelectOptionDict(value="custom", label=default_label)]

        current_op = self._options_data.get(
            CONF_OPERATOR,
            self.config_entry.options.get(
                CONF_OPERATOR, self.config_entry.data.get(CONF_OPERATOR, operator_options[0]["value"])
            ),
        )
        if current_op not in [o["value"] for o in operator_options]:
            current_op = operator_options[0]["value"]

        if user_input is not None:
            chosen_op = user_input[CONF_OPERATOR]
            self._options_data[CONF_OPERATOR] = chosen_op
            op_data = operators.get(chosen_op, {})
            self._options_data["operator_name"] = op_data.get("name", chosen_op.capitalize())
            return await self.async_step_change_offer()

        commodity_name = {
            COMMODITY_ENERGY: "Energia Elettrica",
            COMMODITY_WATER: "Servizio Idrico (Acqua)",
            COMMODITY_GAS: "Gas Naturale",
        }.get(commodity, commodity)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_OPERATOR, default=current_op): SelectSelector(
                    SelectSelectorConfig(options=operator_options, mode=SelectSelectorMode.DROPDOWN)
                ),
            }
        )

        return self.async_show_form(
            step_id="change_operator",
            data_schema=data_schema,
            description_placeholders={"commodity": commodity_name},
        )

    async def async_step_change_offer(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Seleziona l'offerta commerciale per l'operatore scelto."""
        commodity = self.config_entry.data.get(CONF_COMMODITY, COMMODITY_ENERGY)
        operators = load_operators_and_offers(commodity)
        chosen_op = self._options_data.get(
            CONF_OPERATOR,
            self.config_entry.options.get(CONF_OPERATOR, self.config_entry.data.get(CONF_OPERATOR, "custom")),
        )
        op_data = operators.get(chosen_op, {})
        offers = op_data.get("offers", {})

        offer_options = [
            SelectOptionDict(
                value=off_id,
                label=f"{off['name']}" + (f" ({off['description']})" if off.get("description") else ""),
            )
            for off_id, off in offers.items()
        ]
        if not offer_options:
            offer_options = [SelectOptionDict(value="default", label="Offerta Standard")]

        current_offer = self._options_data.get(
            CONF_OFFER,
            self.config_entry.options.get(
                CONF_OFFER, self.config_entry.data.get(CONF_OFFER, offer_options[0]["value"])
            ),
        )
        if current_offer not in [o["value"] for o in offer_options]:
            current_offer = offer_options[0]["value"]

        if user_input is not None:
            chosen_offer_id = user_input[CONF_OFFER]
            self._options_data[CONF_OFFER] = chosen_offer_id
            chosen_offer = offers.get(chosen_offer_id, {})
            self._options_data["offer_name"] = chosen_offer.get("name", chosen_offer_id)

            # Precompila i parametri dell'offerta scelta (escludendo name/id per non sovrascrivere l'istanza)
            for k, v in chosen_offer.items():
                if k not in ("dispbt", "name", "id", "description"):
                    self._options_data[k] = v

            return await self.async_step_params()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_OFFER, default=current_offer): SelectSelector(
                    SelectSelectorConfig(options=offer_options, mode=SelectSelectorMode.DROPDOWN)
                ),
            }
        )

        return self.async_show_form(
            step_id="change_offer",
            data_schema=data_schema,
            description_placeholders={"operator": op_data.get("name", chosen_op.capitalize())},
        )

    async def async_step_water_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Opzioni per il servizio idrico."""
        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v is not None}
            self._options_data.update(clean_input)
            return self.async_create_entry(title="", data=self._options_data)

        entry_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_WATER_SENSOR,
                    description={"suggested_value": entry_data.get(CONF_WATER_SENSOR)},
                ): EntitySelector(EntitySelectorConfig(domain=["sensor", "input_number"])),
                vol.Required(
                    CONF_QF_IDRICO,
                    default=_safe_float(entry_data.get(CONF_QF_IDRICO), 33.60),
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=500.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_QF_FOGNATURA,
                    default=_safe_float(entry_data.get(CONF_QF_FOGNATURA), 4.90),
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=200.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_QF_DEPURAZIONE,
                    default=_safe_float(entry_data.get(CONF_QF_DEPURAZIONE), 14.70),
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=200.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_USA_FOGNATURA,
                    default=_safe_bool(
                        entry_data.get(CONF_USA_FOGNATURA),
                        _safe_bool(entry_data.get(CONF_USA_FOGNATURA_DEPURAZIONE), True),
                    ),
                ): bool,
                vol.Required(
                    CONF_USA_DEPURAZIONE,
                    default=_safe_bool(
                        entry_data.get(CONF_USA_DEPURAZIONE),
                        _safe_bool(entry_data.get(CONF_USA_FOGNATURA_DEPURAZIONE), True),
                    ),
                ): bool,
                vol.Optional(
                    CONF_WATER_ANNUAL_BASELINE,
                    default=_safe_float(entry_data.get(CONF_WATER_ANNUAL_BASELINE), 0.0),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=100000.0, step="any", unit_of_measurement="m³", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_S1, default=_safe_float(entry_data.get(CONF_S1), 55.0)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=500.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S2, default=_safe_float(entry_data.get(CONF_S2), 108.0)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S3, default=_safe_float(entry_data.get(CONF_S3), 162.0)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_S4, default=_safe_float(entry_data.get(CONF_S4), 216.0)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1000.0, step=1.0, unit_of_measurement="m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_AGEVOLATA, default=_safe_float(entry_data.get(CONF_T_AGEVOLATA), 0.4445)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_BASE, default=_safe_float(entry_data.get(CONF_T_BASE), 1.2583)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC1, default=_safe_float(entry_data.get(CONF_T_ECC1), 1.8874)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=10.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC2, default=_safe_float(entry_data.get(CONF_T_ECC2), 2.5166)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=15.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_ECC3, default=_safe_float(entry_data.get(CONF_T_ECC3), 3.7748)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=20.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_FOGNATURA, default=_safe_float(entry_data.get(CONF_T_FOGNATURA), 0.3525)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=5.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_T_DEPURAZIONE, default=_safe_float(entry_data.get(CONF_T_DEPURAZIONE), 0.7049)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=5.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI1, default=_safe_float(entry_data.get(CONF_UI1), 0.004)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI2, default=_safe_float(entry_data.get(CONF_UI2), 0.009)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_UI3, default=_safe_float(entry_data.get(CONF_UI3), 0.005)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=1.0, step="any", unit_of_measurement="€/m³", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_IVA, default=_safe_float(entry_data.get(CONF_IVA), 10.0)
                ): NumberSelector(
                    NumberSelectorConfig(min=0.0, max=50.0, step="any", unit_of_measurement="%", mode=NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="params",
            data_schema=data_schema,
        )

    async def async_step_energy_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Opzioni per la fornitura di energia elettrica."""
        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v is not None}
            self._options_data.update(clean_input)
            return self.async_create_entry(title="", data=self._options_data)

        entry_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_POWER_KW,
                    default=_safe_float(entry_data.get(CONF_POWER_KW), DEFAULT_POWER_KW),
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
                    default=_safe_float(entry_data.get(CONF_CCL), 0.0152),
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
                    default=_safe_float(entry_data.get(CONF_PCV), 69.88),
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
                    CONF_PD,
                    default=_safe_float(entry_data.get(CONF_PD), 0.0018),
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
                    default=_safe_float(entry_data.get(CONF_PD_FORFETTARIO), 0.0),
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
                    default=_safe_bool(entry_data.get(CONF_INCLUDE_LOSSES), True),
                ): bool,
                vol.Required(
                    CONF_ACCISA,
                    default=_safe_float(entry_data.get(CONF_ACCISA), 0.0227),
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
                    default=_safe_float(entry_data.get(CONF_IVA), 10.0),
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
            step_id="params",
            data_schema=data_schema,
        )

    async def async_step_gas_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Opzioni per la fornitura di gas naturale."""
        if user_input is not None:
            clean_input = {k: v for k, v in user_input.items() if v is not None}
            self._options_data.update(clean_input)
            return self.async_create_entry(title="", data=self._options_data)

        entry_data = {**self.config_entry.data, **self.config_entry.options, **self._options_data}

        data_schema = vol.Schema(
            {
                vol.Required(
                    "qf_anno",
                    default=_safe_float(entry_data.get("qf_anno"), 67.32),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=500.0, step="any", unit_of_measurement="€/anno", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    "spread",
                    default=_safe_float(entry_data.get("spread"), 0.085),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=2.0, step="any", unit_of_measurement="€/Smc", mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    CONF_IVA,
                    default=_safe_float(entry_data.get(CONF_IVA), 10.0),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0, max=50.0, step="any", unit_of_measurement="%", mode=NumberSelectorMode.BOX
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="params",
            data_schema=data_schema,
        )
