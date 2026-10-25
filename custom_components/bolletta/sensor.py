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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)

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
    FALLBACK_ARERA,
    OPERATORS,
)
from .tariffs import (
    compute_prezzo_energia,
    compute_prezzo_fisso_giornaliero,
    get_fascia_oraria,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura i sensori Bolletta da ConfigEntry."""
    data = {**entry.data, **entry.options}
    operator = data.get(CONF_OPERATOR, "custom")
    operator_name = OPERATORS.get(operator, operator.capitalize())
    contract_name = data.get("name", f"Bolletta {operator_name}")

    multiorario = data.get(CONF_USE_MULTIORARIO, True)

    entities: list[SensorEntity] = []

    # Sensori Prezzo F0, F1, F2, F3
    f0_sensor = PrezzoEnergiaSensor(hass, entry, "f0", "Prezzo Unitario F0", contract_name, operator_name)
    entities.append(f0_sensor)

    f1_sensor = None
    f2_sensor = None
    f3_sensor = None

    if multiorario:
        f1_sensor = PrezzoEnergiaSensor(hass, entry, "f1", "Prezzo Unitario F1", contract_name, operator_name)
        f2_sensor = PrezzoEnergiaSensor(hass, entry, "f2", "Prezzo Unitario F2", contract_name, operator_name)
        f3_sensor = PrezzoEnergiaSensor(hass, entry, "f3", "Prezzo Unitario F3", contract_name, operator_name)
        entities.extend([f1_sensor, f2_sensor, f3_sensor])

    # Sensore Prezzo Attuale (dinamico in base all'ora e giorno)
    entities.append(
        PrezzoAttualeSensor(
            hass,
            entry,
            "prezzo_attuale",
            "Prezzo Unitario Attuale",
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
        FasciaAttualeSensor(hass, entry, "fascia_attuale", "Fascia Attuale", contract_name, operator_name)
    )

    # Prezzo Fisso Giornaliero
    daily_fixed = PrezzoFissoGiornalieroSensor(
        hass, entry, "prezzo_fisso_giornaliero", "Prezzo Fisso Giornaliero", contract_name, operator_name
    )
    entities.append(daily_fixed)

    # Costo Fisso Mensile Stimato
    entities.append(
        CostoFissoMensileSensor(
            hass, entry, "costo_fisso_mensile", "Costo Fisso Mensile", contract_name, operator_name, daily_fixed
        )
    )

    async_add_entities(entities, True)


class BollettaBaseSensor(SensorEntity):
    """Classe base per i sensori Bolletta."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza il sensore base."""
        self.hass = hass
        self.entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._contract_name = contract_name
        self._operator_name = operator_name

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=contract_name,
            manufacturer=operator_name,
            model="Contratto Fornitura Elettrica",
        )

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
        name: str,
        contract_name: str,
        operator_name: str,
    ) -> None:
        """Inizializza il sensore di prezzo energia."""
        super().__init__(hass, entry, f"prezzo_{fascia}", name, contract_name, operator_name)
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
        pd = float(cfg.get(CONF_PD, 0.0018))
        pd_forfettario = float(cfg.get(CONF_PD_FORFETTARIO, 0.0))
        include_losses = bool(cfg.get(CONF_INCLUDE_LOSSES, True))
        accisa = float(cfg.get(CONF_ACCISA, 0.0227))
        iva = float(cfg.get(CONF_IVA, 10.0))

        # ARERA
        s3 = self._get_float_state(cfg.get(CONF_ARERA_S3), FALLBACK_ARERA["s3"])
        uc3 = self._get_float_state(cfg.get(CONF_ARERA_UC3), FALLBACK_ARERA["uc3"])
        uc6 = self._get_float_state(cfg.get(CONF_ARERA_UC6_QE), FALLBACK_ARERA["uc6_qe"])
        asos = self._get_float_state(cfg.get(CONF_ARERA_ASOS), FALLBACK_ARERA["asos"])
        arim = self._get_float_state(cfg.get(CONF_ARERA_ARIM), FALLBACK_ARERA["arim"])

        self._attr_native_value = compute_prezzo_energia(
            pun=pun,
            ccl=ccl,
            pd=pd,
            pd_forfettario=pd_forfettario,
            s3=s3,
            uc3=uc3,
            uc6=uc6,
            asos=asos,
            arim=arim,
            accisa=accisa,
            iva_percent=iva,
            include_losses=include_losses,
        )


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
        key: str,
        name: str,
        contract_name: str,
        operator_name: str,
        f0_sensor: PrezzoEnergiaSensor,
        f1_sensor: PrezzoEnergiaSensor | None,
        f2_sensor: PrezzoEnergiaSensor | None,
        f3_sensor: PrezzoEnergiaSensor | None,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, key, name, contract_name, operator_name)
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

        for arera_key in [CONF_ARERA_S1, CONF_ARERA_S2, CONF_ARERA_UC6_QP]:
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
        dispbt = float(cfg.get(CONF_DISPBT, -10.77))
        power_kw = float(cfg.get(CONF_POWER_KW, DEFAULT_POWER_KW))
        iva = float(cfg.get(CONF_IVA, 10.0))

        qf = self._get_float_state(cfg.get(CONF_ARERA_S1), FALLBACK_ARERA["s1"])
        qp = self._get_float_state(cfg.get(CONF_ARERA_S2), FALLBACK_ARERA["s2"])
        uc6_qp = self._get_float_state(cfg.get(CONF_ARERA_UC6_QP), FALLBACK_ARERA["uc6_qp"])

        self._attr_native_value = compute_prezzo_fisso_giornaliero(
            pcv=pcv,
            dispbt=dispbt,
            qf_s1=qf,
            qp_s2=qp,
            uc6_qp=uc6_qp,
            power_kw=power_kw,
            iva_percent=iva,
            decimals=4,
        )


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
        key: str,
        name: str,
        contract_name: str,
        operator_name: str,
        daily_sensor: PrezzoFissoGiornalieroSensor,
    ) -> None:
        """Inizializza."""
        super().__init__(hass, entry, key, name, contract_name, operator_name)
        self._daily_sensor = daily_sensor

    def update(self) -> None:
        """Calcola la quota fissa mensile (media 365 / 12 = 30.4167 giorni)."""
        daily_val = self._daily_sensor.native_value
        if daily_val is not None:
            self._attr_native_value = round(daily_val * (365.0 / 12.0), 2)
        else:
            self._attr_native_value = None
