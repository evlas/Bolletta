"""Piattaforma sensori per l'integrazione Bolletta Elettrica."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
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
    DEFAULT_POWER_KW,
    DEFAULT_WATER_VALUES,
    DOMAIN,
    FALLBACK_ARERA,
    OPERATORS,
)
from .operators_loader import load_operators_and_offers
from .tariffs import (
    compute_bolletta_acqua,
    compute_prezzo_energia,
    compute_prezzo_fisso_giornaliero,
    evaluate_formula,
    get_fascia_oraria,
    get_scaglione_acqua,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori Bolletta da ConfigEntry."""
    # Migrazione automatica: aggiorna gli entity_id esistenti nel registro
    # rimuovendo prefissi operatore/offerta e standardizzandoli a sensor.<chiave>
    ent_reg = er.async_get(hass)
    prefix = f"{entry.entry_id}_"
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if reg_entry.domain == "sensor" and reg_entry.unique_id.startswith(prefix):
            key = reg_entry.unique_id[len(prefix):]
            desired_entity_id = f"sensor.{key}"
            if reg_entry.entity_id != desired_entity_id:
                if ent_reg.async_get(desired_entity_id) is None:
                    _LOGGER.info(
                        "Migrazione automatica entity_id per %s da %s a %s",
                        key,
                        reg_entry.entity_id,
                        desired_entity_id,
                    )
                    try:
                        ent_reg.async_update_entity(reg_entry.entity_id, new_entity_id=desired_entity_id)
                    except Exception as err:
                        _LOGGER.warning(
                            "Impossibile migrare entity_id %s in %s: %s",
                            reg_entry.entity_id,
                            desired_entity_id,
                            err,
                        )

    data = {**entry.data, **entry.options}
    commodity = data.get(CONF_COMMODITY, COMMODITY_ENERGY)
    operator = data.get(CONF_OPERATOR, "custom")

    if commodity == COMMODITY_WATER:
        loaded_ops = load_operators_and_offers(COMMODITY_WATER)
        operator_name = loaded_ops.get(operator, {}).get("name", operator.capitalize())
        contract_name = data.get("name") or "Bolletta Acqua"

        annuo_sensor = ConsumoAcquaAnnuoSensor(hass, entry, "consumo_annuo_acqua", contract_name, operator_name)
        totale_sensor = CostoAcquaTotaleSensor(hass, entry, "costo_acqua_totale", contract_name, operator_name, annuo_sensor)
        medio_sensor = PrezzoMedioM3Sensor(hass, entry, "prezzo_medio_m3", contract_name, operator_name, totale_sensor)
        scaglione_sensor = ScaglioneAcquaSensor(hass, entry, "scaglione_acqua", contract_name, operator_name, totale_sensor)
        qf_day_sensor = QuotaFissaGiornalieraAcquaSensor(hass, entry, "quota_fissa_giornaliera_acqua", contract_name, operator_name, totale_sensor)
        qf_year_sensor = QuotaFissaAnnuaAcquaSensor(hass, entry, "quota_fissa_annua_acqua", contract_name, operator_name, totale_sensor)
        qv_sensor = QuotaVariabileAcquaSensor(hass, entry, "quota_variabile_acqua", contract_name, operator_name, totale_sensor)

        async_add_entities([annuo_sensor, totale_sensor, medio_sensor, scaglione_sensor, qf_day_sensor, qf_year_sensor, qv_sensor], True)
        return

    if commodity == COMMODITY_GAS:
        loaded_ops = load_operators_and_offers(COMMODITY_GAS)
        operator_name = loaded_ops.get(operator, {}).get("name", operator.capitalize())
        contract_name = data.get("name") or "Bolletta Gas"
        # Al momento la commodity gas non espone sensori complessi
        return

    # Default: Energia Elettrica
    loaded_ops = load_operators_and_offers(COMMODITY_ENERGY)
    operator_name = loaded_ops.get(operator, {}).get("name", OPERATORS.get(operator, operator.capitalize()))
    contract_name = data.get("name") or "Bolletta Luce"

    multiorario = data.get(CONF_USE_MULTIORARIO, True)

    entities: list[SensorEntity] = []

    # Sensori Prezzo F0, F1, F2, F3
    f0_sensor = PrezzoEnergiaSensor(hass, entry, "f0", "prezzo_unitario_f0", contract_name, operator_name)
    entities.append(f0_sensor)

    f1_sensor = None
    f2_sensor = None
    f3_sensor = None

    if multiorario:
        f1_sensor = PrezzoEnergiaSensor(hass, entry, "f1", "prezzo_unitario_f1", contract_name, operator_name)
        f2_sensor = PrezzoEnergiaSensor(hass, entry, "f2", "prezzo_unitario_f2", contract_name, operator_name)
        f3_sensor = PrezzoEnergiaSensor(hass, entry, "f3", "prezzo_unitario_f3", contract_name, operator_name)
        entities.extend([f1_sensor, f2_sensor, f3_sensor])

    # Sensore Prezzo Attuale (dinamico in base all'ora e giorno)
    entities.append(
        PrezzoAttualeSensor(
            hass,
            entry,
            "prezzo_unitario_attuale",
            contract_name,
            operator_name,
            f0_sensor,
            f1_sensor,
            f2_sensor,
            f3_sensor,
        )
    )

    # Sensore Fascia Attuale (F1, F2, F3)
    entities.append(
        FasciaAttualeSensor(hass, entry, "fascia_attuale", contract_name, operator_name)
    )

    # Prezzo Fisso Giornaliero
    daily_fixed = PrezzoFissoGiornalieroSensor(
        hass, entry, "prezzo_fisso_giornaliero", contract_name, operator_name
    )
    entities.append(daily_fixed)

    # Costo Fisso Mensile Stimato
    entities.append(
        CostoFissoMensileSensor(
            hass, entry, "costo_fisso_mensile", contract_name, operator_name, daily_fixed
        )
    )

    # Potenza Impegnata da Contratto (kW)
    entities.append(
        PotenzaImpegnataSensor(
            hass, entry, "potenza_impegnata", contract_name, operator_name
        )
    )

    async_add_entities(entities, True)


SENSOR_NAMES: dict[str, str] = {
    # Energia Elettrica
    "prezzo_unitario_f0": "Prezzo Unitario F0",
    "prezzo_unitario_f1": "Prezzo Unitario F1",
    "prezzo_unitario_f2": "Prezzo Unitario F2",
    "prezzo_unitario_f3": "Prezzo Unitario F3",
    "prezzo_unitario_attuale": "Prezzo Unitario Attuale",
    "fascia_attuale": "Fascia Attuale",
    "prezzo_fisso_giornaliero": "Prezzo Fisso Giornaliero",
    "costo_fisso_mensile": "Costo Fisso Mensile",
    "potenza_impegnata": "Potenza Impegnata",
    # Servizio Idrico
    "consumo_annuo_acqua": "Consumo Annuo Acqua",
    "costo_acqua_totale": "Costo Totale Acqua",
    "prezzo_medio_m3": "Prezzo Medio al m³",
    "scaglione_acqua": "Scaglione Idrico Attivo",
    "quota_fissa_giornaliera_acqua": "Quota Fissa Giornaliera Acqua",
    "quota_fissa_annua_acqua": "Quota Fissa Annua Acqua",
    "quota_variabile_acqua": "Quota Variabile Consumo Acqua",
}


class BollettaBaseSensor(SensorEntity):
    """Classe base per i sensori Bolletta."""

    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza il sensore base."""
        self.hass = hass
        self.entry = entry
        self._key = translation_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"
        self._contract_name = contract_name
        self._operator_name = operator_name
        self._attr_name = SENSOR_NAMES.get(translation_key, translation_key.replace("_", " ").title())

        commodity = entry.data.get(CONF_COMMODITY, COMMODITY_ENERGY)
        offer_name = entry.options.get("offer_name", entry.data.get("offer_name", ""))
        model_name = {
            COMMODITY_ENERGY: f"Fornitura Energia Elettrica ({operator_name}{f' - {offer_name}' if offer_name else ''})",
            COMMODITY_WATER: f"Servizio Idrico ({operator_name}{f' - {offer_name}' if offer_name else ''})",
            COMMODITY_GAS: f"Fornitura Gas ({operator_name}{f' - {offer_name}' if offer_name else ''})",
        }.get(commodity, f"Fornitura {operator_name}")

        entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        version = entry_data.get("version") if isinstance(entry_data, dict) else None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=contract_name,
            manufacturer=operator_name,
            model=model_name,
            sw_version=str(version) if version else "1.0.0",
        )

    @property
    def suggested_object_id(self) -> str | None:
        """Suggerisce l'ID entità generico senza prefisso operatore o offerta."""
        return self._key

    @property
    def config(self) -> dict[str, Any]:
        """Restituisce le opzioni correnti unite ai dati iniziali."""
        return {**self.entry.data, **self.entry.options}

    def _get_float_state(self, entity_id: str | None, default_val: float = 0.0) -> float:
        """Legge lo stato numerico di un'entità Home Assistant."""
        if not entity_id:
            return default_val
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return default_val
        try:
            return float(state.state.replace(",", "."))
        except (ValueError, TypeError):
            return default_val


class PrezzoEnergiaSensor(BollettaBaseSensor):
    """Sensore per il prezzo dell'energia (€/kWh) per una determinata fascia."""

    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 6
    _attr_icon = "mdi:cash-fast"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        fascia: str,
        translation_key: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza il sensore di prezzo energia."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._fascia = fascia
        self._attr_native_value: float | None = None

    async def async_added_to_hass(self) -> None:
        """Registra i listener di aggiornamento sugli stati delle entità collegate."""
        await super().async_added_to_hass()

        watched_entities: set[str] = set()

        cfg = self.config
        pun_key = f"pun_{self._fascia}"
        if cfg.get(pun_key):
            watched_entities.add(cfg[pun_key])

        for arera_key in [
            CONF_ARERA_S3,
            CONF_ARERA_UC3,
            CONF_ARERA_UC6_QE,
            CONF_ARERA_ASOS,
            CONF_ARERA_ARIM,
        ]:
            if cfg.get(arera_key):
                watched_entities.add(cfg[arera_key])

        @callback
        def _handle_state_change(event) -> None:
            self.async_schedule_update_ha_state(True)

        if watched_entities:
            self.async_on_remove(
                async_track_state_change_event(self.hass, list(watched_entities), _handle_state_change)
            )

    def update(self) -> None:
        """Calcola il prezzo unitario al kWh."""
        cfg = self.config
        pun_entity = cfg.get(f"pun_{self._fascia}")
        pun = self._get_float_state(pun_entity, 0.0)

        # Se F0 non ha un sensore dedicato ma è impostato F1/F2/F3, usa fallback F1
        if self._fascia == "f0" and pun == 0.0:
            f1_entity = cfg.get(CONF_PUN_F1)
            if f1_entity:
                pun = self._get_float_state(f1_entity, 0.0)

        ccl = float(cfg.get(CONF_CCL, 0.0152))
        pcv = float(cfg.get(CONF_PCV, 69.88))
        pd = float(cfg.get(CONF_PD, 0.0018))
        pd_forfettario = float(cfg.get(CONF_PD_FORFETTARIO, 0.0))
        include_losses = bool(cfg.get(CONF_INCLUDE_LOSSES, True))
        accisa = float(cfg.get(CONF_ACCISA, 0.0227))
        iva = float(cfg.get(CONF_IVA, 10.0))
        power_kw = float(cfg.get(CONF_POWER_KW, DEFAULT_POWER_KW))

        # ARERA
        s1 = self._get_float_state(cfg.get(CONF_ARERA_S1), FALLBACK_ARERA["s1"])
        s2 = self._get_float_state(cfg.get(CONF_ARERA_S2), FALLBACK_ARERA["s2"])
        s3 = self._get_float_state(cfg.get(CONF_ARERA_S3), FALLBACK_ARERA["s3"])
        uc3 = self._get_float_state(cfg.get(CONF_ARERA_UC3), FALLBACK_ARERA["uc3"])
        uc6_qe = self._get_float_state(cfg.get(CONF_ARERA_UC6_QE), FALLBACK_ARERA["uc6_qe"])
        uc6_qp = self._get_float_state(cfg.get(CONF_ARERA_UC6_QP), FALLBACK_ARERA["uc6_qp"])
        asos = self._get_float_state(cfg.get(CONF_ARERA_ASOS), FALLBACK_ARERA["asos"])
        arim = self._get_float_state(cfg.get(CONF_ARERA_ARIM), FALLBACK_ARERA["arim"])
        dispbt = self._get_float_state(cfg.get(CONF_ARERA_DISPBT), FALLBACK_ARERA["dispbt"])

        context = {
            "pun": pun,
            "ccl": ccl,
            "pcv": pcv,
            "pd": pd,
            "pd_forfettario": pd_forfettario,
            "include_losses": include_losses,
            "accisa": accisa,
            "iva": iva,
            "power_kw": power_kw,
            "s1": s1,
            "s2": s2,
            "s3": s3,
            "uc3": uc3,
            "uc6_qe": uc6_qe,
            "uc6_qp": uc6_qp,
            "asos": asos,
            "arim": arim,
            "dispbt": dispbt,
        }
        for k, v in cfg.items():
            if k not in context and isinstance(v, (int, float, bool)):
                context[k] = v

        fallback = compute_prezzo_energia(
            pun=pun,
            ccl=ccl,
            pd=pd,
            pd_forfettario=pd_forfettario,
            s3=s3,
            uc3=uc3,
            uc6=uc6_qe,
            asos=asos,
            arim=arim,
            accisa=accisa,
            iva_percent=iva,
            include_losses=include_losses,
        )

        formula = cfg.get(CONF_FORMULA_ENERGIA)
        if formula:
            self._attr_native_value = round(evaluate_formula(formula, context, default=fallback), 6)
        else:
            self._attr_native_value = fallback


class PrezzoAttualeSensor(BollettaBaseSensor):
    """Sensore dinamico che riflette il prezzo della fascia oraria attualmente attiva."""

    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 6
    _attr_icon = "mdi:lightning-bolt-circle"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        f0_sensor: PrezzoEnergiaSensor,
        f1_sensor: PrezzoEnergiaSensor | None,
        f2_sensor: PrezzoEnergiaSensor | None,
        f3_sensor: PrezzoEnergiaSensor | None,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._f0 = f0_sensor
        self._f1 = f1_sensor
        self._f2 = f2_sensor
        self._f3 = f3_sensor
        self._attr_native_value: float | None = None

    async def async_added_to_hass(self) -> None:
        """Aggiorna ogni minuto per catturare il cambio di fascia."""
        await super().async_added_to_hass()

        @callback
        def _tick(now: datetime) -> None:
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_time_interval(self.hass, _tick, timedelta(minutes=1))
        )

    def update(self) -> None:
        """Seleziona il valore del sensore corrispondente alla fascia oraria attiva."""
        cfg = self.config
        multiorario = cfg.get(CONF_USE_MULTIORARIO, True)

        if not multiorario or not (self._f1 and self._f2 and self._f3):
            self._attr_native_value = self._f0.native_value
            self._attr_extra_state_attributes = {"fascia": "F0"}
            return

        fascia = get_fascia_oraria()
        if fascia == "F1" and self._f1:
            val = self._f1.native_value
        elif fascia == "F2" and self._f2:
            val = self._f2.native_value
        else:
            val = self._f3.native_value if self._f3 else self._f0.native_value

        self._attr_native_value = val
        self._attr_extra_state_attributes = {"fascia": fascia}


class FasciaAttualeSensor(BollettaBaseSensor):
    """Sensore che indica la fascia oraria corrente (F1, F2 o F3)."""

    _attr_icon = "mdi:calendar-clock"

    async def async_added_to_hass(self) -> None:
        """Aggiorna lo stato ogni minuto."""
        await super().async_added_to_hass()

        @callback
        def _tick(now: datetime) -> None:
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_time_interval(self.hass, _tick, timedelta(minutes=1))
        )

    def update(self) -> None:
        """Aggiorna la fascia corrente."""
        self._attr_native_value = get_fascia_oraria()


class PrezzoFissoGiornalieroSensor(BollettaBaseSensor):
    """Sensore per la quota fissa giornaliera (€/giorno)."""

    _attr_native_unit_of_measurement = "EUR/day"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4
    _attr_icon = "mdi:calendar-today"

    async def async_added_to_hass(self) -> None:
        """Registra i listener di aggiornamento."""
        await super().async_added_to_hass()

        watched_entities: set[str] = set()
        cfg = self.config

        for arera_key in [CONF_ARERA_S1, CONF_ARERA_S2, CONF_ARERA_UC6_QP, CONF_ARERA_DISPBT]:
            if cfg.get(arera_key):
                watched_entities.add(cfg[arera_key])

        @callback
        def _handle_state_change(event) -> None:
            self.async_schedule_update_ha_state(True)

        if watched_entities:
            self.async_on_remove(
                async_track_state_change_event(self.hass, list(watched_entities), _handle_state_change)
            )

    def update(self) -> None:
        """Calcola la quota fissa giornaliera."""
        cfg = self.config
        pcv = float(cfg.get(CONF_PCV, 69.88))
        dispbt = self._get_float_state(cfg.get(CONF_ARERA_DISPBT), FALLBACK_ARERA["dispbt"])
        power_kw = float(cfg.get(CONF_POWER_KW, DEFAULT_POWER_KW))
        iva = float(cfg.get(CONF_IVA, 10.0))

        qf = self._get_float_state(cfg.get(CONF_ARERA_S1), FALLBACK_ARERA["s1"])
        qp = self._get_float_state(cfg.get(CONF_ARERA_S2), FALLBACK_ARERA["s2"])
        uc6_qp = self._get_float_state(cfg.get(CONF_ARERA_UC6_QP), FALLBACK_ARERA["uc6_qp"])

        context = {
            "pcv": pcv,
            "dispbt": dispbt,
            "s1": qf,
            "s2": qp,
            "uc6_qp": uc6_qp,
            "power_kw": power_kw,
            "iva": iva,
            "ccl": float(cfg.get(CONF_CCL, 0.0152)),
            "pd": float(cfg.get(CONF_PD, 0.0018)),
            "accisa": float(cfg.get(CONF_ACCISA, 0.0227)),
        }
        for k, v in cfg.items():
            if k not in context and isinstance(v, (int, float, bool)):
                context[k] = v

        fallback = compute_prezzo_fisso_giornaliero(
            pcv=pcv,
            dispbt=dispbt,
            qf_s1=qf,
            qp_s2=qp,
            uc6_qp=uc6_qp,
            power_kw=power_kw,
            iva_percent=iva,
            decimals=4,
        )

        formula = cfg.get(CONF_FORMULA_QUOTA_FISSA)
        if formula:
            self._attr_native_value = round(evaluate_formula(formula, context, default=fallback), 4)
        else:
            self._attr_native_value = fallback


class CostoFissoMensileSensor(BollettaBaseSensor):
    """Sensore per la stima della quota fissa mensile (€/mese)."""

    _attr_native_unit_of_measurement = "EUR/month"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:calendar-month"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        daily_sensor: PrezzoFissoGiornalieroSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._daily_sensor = daily_sensor

    def update(self) -> None:
        """Calcola la quota fissa mensile (media 365 / 12 = 30.4167 giorni)."""
        daily_val = self._daily_sensor.native_value
        if daily_val is not None:
            self._attr_native_value = round(daily_val * (365.0 / 12.0), 2)
        else:
            self._attr_native_value = None


class PotenzaImpegnataSensor(BollettaBaseSensor):
    """Sensore per la potenza contrattuale impegnata (kW)."""

    _attr_native_unit_of_measurement = "kW"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:flash"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza il sensore potenza impegnata."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._power_kw = float(self.config.get(CONF_POWER_KW, DEFAULT_POWER_KW))

    def update(self) -> None:
        """Aggiorna il valore della potenza impegnata dalle opzioni."""
        self._power_kw = float(self.config.get(CONF_POWER_KW, DEFAULT_POWER_KW))
        self._attr_native_value = self._power_kw

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Restituisce attributi utili per automazioni e controllo carichi."""
        power_kw = self._power_kw
        potenza_disp_kw = round(power_kw * 1.10, 2)
        potenza_disp_w = int(round(power_kw * 1100))
        testo_kw = f"{str(power_kw).replace('.', ',').rstrip('0').rstrip(',') if power_kw % 1 != 0 else int(power_kw)} kW"

        # Soglie standard controllo carichi contatore elettronico Open Meter / ARERA
        if abs(power_kw - 3.0) < 0.1:
            soglia_innesco_w = 3299
            soglia_istantanea_w = 3999
        elif abs(power_kw - 4.5) < 0.1:
            soglia_innesco_w = 4949
            soglia_istantanea_w = 5899
        elif abs(power_kw - 6.0) < 0.1:
            soglia_innesco_w = 6599
            soglia_istantanea_w = 7899
        elif abs(power_kw - 10.0) < 0.1:
            soglia_innesco_w = 10999
            soglia_istantanea_w = 12999
        else:
            soglia_innesco_w = int(round(power_kw * 1100 - 1))
            soglia_istantanea_w = int(round(power_kw * 1333 - 1))

        return {
            "potenza_impegnata_w": int(round(power_kw * 1000)),
            "potenza_disponibile_kw": potenza_disp_kw,
            "potenza_disponibile_w": potenza_disp_w,
            "soglia_innesco_w": soglia_innesco_w,
            "soglia_istantanea_w": soglia_istantanea_w,
            "selettore_kw_testo": testo_kw,
        }


# =============================================================================
# SENSORI PER IL SERVIZIO IDRICO (ACQUA)
# =============================================================================
class ConsumoAcquaAnnuoSensor(BollettaBaseSensor, RestoreEntity):
    """Sensore per la contabilizzazione dell'acqua consumata dal 1° gennaio al 31 dicembre di ogni anno."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = "m³"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 3
    _attr_icon = "mdi:water"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._current_year = datetime.now().year
        self._baseline_reading: float | None = None
        self._attr_native_value: float = 0.0

    @property
    def baseline_reading(self) -> float:
        """Restituisce la lettura al 1° gennaio."""
        return self._baseline_reading or 0.0

    async def async_added_to_hass(self) -> None:
        """Ripristina lo stato precedente e registra i listener di aggiornamento e reset annuale."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        now = datetime.now()
        current_year = now.year

        if last_state and last_state.attributes:
            stored_year = last_state.attributes.get("anno_solare")
            stored_baseline = last_state.attributes.get("lettura_iniziale_anno")
            if stored_year == current_year and stored_baseline is not None:
                self._baseline_reading = float(stored_baseline)
                self._current_year = current_year

        cfg_baseline = self.config.get(CONF_WATER_ANNUAL_BASELINE)
        if cfg_baseline is not None and float(cfg_baseline) > 0:
            self._baseline_reading = float(cfg_baseline)

        water_entity = self.config.get(CONF_WATER_SENSOR)

        @callback
        def _handle_state_change(event) -> None:
            self.async_schedule_update_ha_state(True)

        if water_entity:
            self.async_on_remove(
                async_track_state_change_event(self.hass, [water_entity], _handle_state_change)
            )

        @callback
        def _check_midnight_reset(now_dt: datetime) -> None:
            if now_dt.year != self._current_year:
                _LOGGER.info(
                    "Cambio anno solare per %s (%s -> %s). Azzeramento contabilizzazione acqua al 1° Gennaio.",
                    self.entity_id,
                    self._current_year,
                    now_dt.year,
                )
                self._current_year = now_dt.year
                water_ent = self.config.get(CONF_WATER_SENSOR)
                current_mc = self._get_float_state(water_ent, 0.0)
                self._baseline_reading = current_mc
                self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_time_change(
                self.hass, _check_midnight_reset, hour=0, minute=0, second=5
            )
        )

    def update(self) -> None:
        """Calcola il consumo d'acqua maturato nell'anno solare in corso (1 Gen - 31 Dic)."""
        now = datetime.now()
        water_entity = self.config.get(CONF_WATER_SENSOR)
        raw_mc = self._get_float_state(water_entity, 0.0)

        if now.year != self._current_year:
            self._current_year = now.year
            self._baseline_reading = raw_mc

        if self._baseline_reading is None:
            cfg_baseline = self.config.get(CONF_WATER_ANNUAL_BASELINE)
            if cfg_baseline is not None and float(cfg_baseline) > 0:
                self._baseline_reading = float(cfg_baseline)
            else:
                self._baseline_reading = 0.0

        if raw_mc < self._baseline_reading:
            self._baseline_reading = 0.0

        consumo_annuo = max(0.0, raw_mc - self._baseline_reading)
        self._attr_native_value = round(consumo_annuo, 3)

        self._attr_extra_state_attributes = {
            "periodo_contabilizzazione": f"01/01/{self._current_year} - 31/12/{self._current_year}",
            "anno_solare": self._current_year,
            "lettura_iniziale_anno": self._baseline_reading,
            "lettura_contatore_grezza": raw_mc,
            "prossimo_reset": f"01/01/{self._current_year + 1} 00:00:00",
        }


class CostoAcquaTotaleSensor(BollettaBaseSensor):
    """Sensore per il costo totale stimato della bolletta dell'acqua (€)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:water-pump"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        annuo_sensor: ConsumoAcquaAnnuoSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._annuo_sensor = annuo_sensor
        self.calc_result: dict[str, Any] = {
            "costo_totale": 0.0,
            "prezzo_medio_m3": 0.0,
            "scaglione": "Agevolata",
            "quota_fissa_giornaliera": 0.0,
            "quota_fissa_annua": 0.0,
            "quota_variabile": 0.0,
        }

    async def async_added_to_hass(self) -> None:
        """Ascolta le variazioni del contatore acqua e del sensore annuo."""
        await super().async_added_to_hass()
        water_entity = self.config.get(CONF_WATER_SENSOR)

        @callback
        def _handle_state_change(event) -> None:
            self.async_schedule_update_ha_state(True)

        watched = [e for e in [water_entity, self._annuo_sensor.entity_id] if e]
        if watched:
            self.async_on_remove(
                async_track_state_change_event(self.hass, watched, _handle_state_change)
            )

    def update(self) -> None:
        """Calcola il costo dell'acqua basandosi sul consumo dell'anno solare (1 Gen - 31 Dic)."""
        cfg = self.config
        mc = float(self._annuo_sensor.native_value) if self._annuo_sensor.native_value is not None else 0.0

        usa_fog = bool(cfg.get(CONF_USA_FOGNATURA, cfg.get(CONF_USA_FOGNATURA_DEPURAZIONE, True)))
        usa_dep = bool(cfg.get(CONF_USA_DEPURAZIONE, cfg.get(CONF_USA_FOGNATURA_DEPURAZIONE, True)))

        self.calc_result = compute_bolletta_acqua(
            mc=mc,
            qf_idrico=float(cfg.get(CONF_QF_IDRICO, DEFAULT_WATER_VALUES[CONF_QF_IDRICO])),
            qf_fognatura=float(cfg.get(CONF_QF_FOGNATURA, DEFAULT_WATER_VALUES[CONF_QF_FOGNATURA])),
            qf_depurazione=float(cfg.get(CONF_QF_DEPURAZIONE, DEFAULT_WATER_VALUES[CONF_QF_DEPURAZIONE])),
            usa_fognatura=usa_fog,
            usa_depurazione=usa_dep,
            s1=float(cfg.get(CONF_S1, DEFAULT_WATER_VALUES[CONF_S1])),
            s2=float(cfg.get(CONF_S2, DEFAULT_WATER_VALUES[CONF_S2])),
            s3=float(cfg.get(CONF_S3, DEFAULT_WATER_VALUES[CONF_S3])),
            s4=float(cfg.get(CONF_S4, DEFAULT_WATER_VALUES[CONF_S4])),
            t_agevolata=float(cfg.get(CONF_T_AGEVOLATA, DEFAULT_WATER_VALUES[CONF_T_AGEVOLATA])),
            t_base=float(cfg.get(CONF_T_BASE, DEFAULT_WATER_VALUES[CONF_T_BASE])),
            t_ecc1=float(cfg.get(CONF_T_ECC1, DEFAULT_WATER_VALUES[CONF_T_ECC1])),
            t_ecc2=float(cfg.get(CONF_T_ECC2, DEFAULT_WATER_VALUES[CONF_T_ECC2])),
            t_ecc3=float(cfg.get(CONF_T_ECC3, DEFAULT_WATER_VALUES[CONF_T_ECC3])),
            t_fognatura=float(cfg.get(CONF_T_FOGNATURA, DEFAULT_WATER_VALUES[CONF_T_FOGNATURA])),
            t_depurazione=float(cfg.get(CONF_T_DEPURAZIONE, DEFAULT_WATER_VALUES[CONF_T_DEPURAZIONE])),
            ui1=float(cfg.get(CONF_UI1, DEFAULT_WATER_VALUES[CONF_UI1])),
            ui2=float(cfg.get(CONF_UI2, DEFAULT_WATER_VALUES[CONF_UI2])),
            ui3=float(cfg.get(CONF_UI3, DEFAULT_WATER_VALUES[CONF_UI3])),
            iva_percent=float(cfg.get(CONF_IVA, 10.0)),
        )

        self._attr_native_value = self.calc_result["costo_totale"]
        self._attr_extra_state_attributes = {
            "consumo_annuo_mc": mc,
            "periodo_contabilizzazione": f"01/01/{datetime.now().year} - 31/12/{datetime.now().year}",
            "scaglione": self.calc_result["scaglione"],
            "quota_fissa_annua": self.calc_result["quota_fissa_annua"],
            "quota_variabile": self.calc_result["quota_variabile"],
            "fognatura_attiva": usa_fog,
            "depurazione_attiva": usa_dep,
        }


class PrezzoMedioM3Sensor(BollettaBaseSensor):
    """Sensore per il prezzo medio effettivo al m³ (€/m³)."""

    _attr_native_unit_of_measurement = "EUR/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4
    _attr_icon = "mdi:water-percent"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        totale_sensor: CostoAcquaTotaleSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._totale_sensor = totale_sensor

    def update(self) -> None:
        """Aggiorna il prezzo medio."""
        self._attr_native_value = self._totale_sensor.calc_result.get("prezzo_medio_m3", 0.0)


class ScaglioneAcquaSensor(BollettaBaseSensor):
    """Sensore per lo scaglione idrico attualmente attivo."""

    _attr_icon = "mdi:stairs"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        totale_sensor: CostoAcquaTotaleSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._totale_sensor = totale_sensor

    def update(self) -> None:
        """Aggiorna lo scaglione."""
        self._attr_native_value = self._totale_sensor.calc_result.get("scaglione", "Agevolata")


class QuotaFissaGiornalieraAcquaSensor(BollettaBaseSensor):
    """Sensore per la quota fissa giornaliera dell'acqua (€/giorno)."""

    _attr_native_unit_of_measurement = "EUR/day"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4
    _attr_icon = "mdi:calendar-today"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        totale_sensor: CostoAcquaTotaleSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._totale_sensor = totale_sensor

    def update(self) -> None:
        """Aggiorna la quota fissa giornaliera."""
        self._attr_native_value = self._totale_sensor.calc_result.get("quota_fissa_giornaliera", 0.0)


class QuotaFissaAnnuaAcquaSensor(BollettaBaseSensor):
    """Sensore per la quota fissa annua dell'acqua (€/anno)."""

    _attr_native_unit_of_measurement = "EUR/year"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:calendar-blank"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        totale_sensor: CostoAcquaTotaleSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._totale_sensor = totale_sensor

    def update(self) -> None:
        """Aggiorna la quota fissa annua."""
        self._attr_native_value = self._totale_sensor.calc_result.get("quota_fissa_annua", 0.0)


class QuotaVariabileAcquaSensor(BollettaBaseSensor):
    """Sensore per la quota variabile dell'acqua (€)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:water-plus"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        translation_key: str,
        contract_name: str,
        operator_name: str,
        totale_sensor: CostoAcquaTotaleSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, translation_key, contract_name, operator_name)
        self._totale_sensor = totale_sensor

    def update(self) -> None:
        """Aggiorna la quota variabile."""
        self._attr_native_value = self._totale_sensor.calc_result.get("quota_variabile", 0.0)

