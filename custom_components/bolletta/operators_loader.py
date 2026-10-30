"""Modulo per il caricamento dinamico di operatori e offerte per energia, acqua e gas."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .const import (
    DEFAULT_FORMULA_ENERGIA,
    DEFAULT_FORMULA_QUOTA_FISSA,
    DEFAULT_WATER_VALUES,
    COMMODITY_ENERGY,
    COMMODITY_WATER,
    COMMODITY_GAS,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_OFFER_VALUES = {
    "ccl": 0.0150,
    "pcv": 90.00,
    "pd": 0.0018,
    "pd_forfettario": 0.0,
    "include_losses": True,
    "accisa": 0.0227,
    "iva": 10.0,
    "formula_energia": DEFAULT_FORMULA_ENERGIA,
    "formula_quota_fissa": DEFAULT_FORMULA_QUOTA_FISSA,
}


def _parse_xml_offer(file_path: Path, commodity: str = "energy") -> dict[str, Any]:
    """Estrae i dati e le formule di calcolo di un'offerta da un file XML."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    def get_text(tag: str, default: str = "") -> str:
        elem = root.find(tag)
        return elem.text.strip() if elem is not None and elem.text else default

    def get_float(tag: str, default: float) -> float:
        val = get_text(tag)
        try:
            return float(val) if val else default
        except ValueError:
            return default

    def get_bool(tag: str, default: bool) -> bool:
        val = get_text(tag).lower()
        if val in ("true", "1", "yes", "si"):
            return True
        if val in ("false", "0", "no"):
            return False
        return default

    offer_id = get_text("id", file_path.stem)
    name = get_text("name", offer_id.replace("_", " ").title())
    desc = get_text("description", "")

    data: dict[str, Any] = {
        "id": offer_id,
        "name": name,
        "description": desc,
    }

    if commodity == "energy":
        data.update({
            "ccl": get_float("ccl", DEFAULT_OFFER_VALUES["ccl"]),
            "pcv": get_float("pcv", DEFAULT_OFFER_VALUES["pcv"]),
            "pd": get_float("pd", DEFAULT_OFFER_VALUES["pd"]),
            "pd_forfettario": get_float("pd_forfettario", DEFAULT_OFFER_VALUES["pd_forfettario"]),
            "include_losses": get_bool("include_losses", DEFAULT_OFFER_VALUES["include_losses"]),
            "accisa": get_float("accisa", DEFAULT_OFFER_VALUES["accisa"]),
            "iva": get_float("iva", DEFAULT_OFFER_VALUES["iva"]),
            "formula_energia": get_text("formula_energia", DEFAULT_FORMULA_ENERGIA),
            "formula_quota_fissa": get_text("formula_quota_fissa", DEFAULT_FORMULA_QUOTA_FISSA),
        })
    elif commodity == "water":
        for k, v in DEFAULT_WATER_VALUES.items():
            if isinstance(v, bool):
                data[k] = get_bool(k, v)
            elif isinstance(v, (int, float)):
                data[k] = get_float(k, float(v))
            else:
                data[k] = get_text(k, str(v))

    # Memorizza eventuali altri tag personalizzati
    for child in root:
        if child.tag not in data and child.text:
            text = child.text.strip()
            try:
                data[child.tag] = float(text)
            except ValueError:
                data[child.tag] = text

    return data


def _parse_json_offer(file_path: Path, commodity: str = "energy") -> dict[str, Any]:
    """Estrae i dati e le formule di calcolo di un'offerta da un file JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    offer_id = raw_data.get("id", file_path.stem)
    name = raw_data.get("name", offer_id.replace("_", " ").title())
    desc = raw_data.get("description", "")

    data: dict[str, Any] = dict(raw_data)
    data["id"] = offer_id
    data["name"] = name
    data["description"] = desc

    if commodity == "energy":
        data.setdefault("ccl", DEFAULT_OFFER_VALUES["ccl"])
        data.setdefault("pcv", DEFAULT_OFFER_VALUES["pcv"])
        data.setdefault("pd", DEFAULT_OFFER_VALUES["pd"])
        data.setdefault("pd_forfettario", DEFAULT_OFFER_VALUES["pd_forfettario"])
        data.setdefault("include_losses", DEFAULT_OFFER_VALUES["include_losses"])
        data.setdefault("accisa", DEFAULT_OFFER_VALUES["accisa"])
        data.setdefault("iva", DEFAULT_OFFER_VALUES["iva"])
        data.setdefault("formula_energia", DEFAULT_FORMULA_ENERGIA)
        data.setdefault("formula_quota_fissa", DEFAULT_FORMULA_QUOTA_FISSA)
        data.pop("dispbt", None)
    elif commodity == "water":
        for k, v in DEFAULT_WATER_VALUES.items():
            data.setdefault(k, v)
    elif commodity == "gas":
        data.setdefault("spread", 0.05)
        data.setdefault("qf_anno", 96.0)
        data.setdefault("iva", 10.0)

    return data


def load_operators_and_offers(
    commodity: str = "energy", base_dir: Path | None = None
) -> dict[str, dict[str, Any]]:
    """Effettua la scansione della cartella operators per la commodity specificata."""
    if base_dir is None:
        root_operators = Path(__file__).parent / "operators"
        commodity_dir = root_operators / commodity
        if commodity_dir.exists():
            base_dir = commodity_dir
        else:
            base_dir = root_operators

    operators: dict[str, dict[str, Any]] = {}

    if not base_dir.exists():
        _LOGGER.warning("Cartella operatori %s non trovata", base_dir)
        return operators

    for op_dir in sorted(base_dir.iterdir()):
        if not op_dir.is_dir() or op_dir.name.startswith("."):
            continue

        # Evita di considerare sottodirectory commodity se chiamata sulla root
        if op_dir.name in ("energy", "water", "gas") and base_dir.name == "operators":
            continue

        op_id = op_dir.name
        op_name = op_id.capitalize()

        # Verifica eventuale file operatore (operator.json o operator.xml)
        op_json = op_dir / "operator.json"
        op_xml = op_dir / "operator.xml"

        if op_json.exists():
            try:
                with open(op_json, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    op_name = meta.get("name", op_name)
                    op_id = meta.get("id", op_id)
            except Exception as err:
                _LOGGER.warning("Errore lettura %s: %s", op_json, err)
        elif op_xml.exists():
            try:
                tree = ET.parse(op_xml)
                root = tree.getroot()
                name_elem = root.find("name")
                if name_elem is not None and name_elem.text:
                    op_name = name_elem.text.strip()
                id_elem = root.find("id")
                if id_elem is not None and id_elem.text:
                    op_id = id_elem.text.strip()
            except Exception as err:
                _LOGGER.warning("Errore lettura %s: %s", op_xml, err)

        offers: dict[str, dict[str, Any]] = {}

        # Cerca file di offerta JSON e XML
        for file in sorted(op_dir.iterdir()):
            if file.name in ("operator.json", "operator.xml") or file.name.startswith("."):
                continue

            try:
                if file.suffix.lower() == ".json":
                    offer_data = _parse_json_offer(file, commodity=commodity)
                    offers[offer_data["id"]] = offer_data
                elif file.suffix.lower() == ".xml":
                    offer_data = _parse_xml_offer(file, commodity=commodity)
                    offers[offer_data["id"]] = offer_data
            except Exception as err:
                _LOGGER.error("Errore nel parsing dell'offerta %s: %s", file, err)

        # Se non ci sono offerte, crea un'offerta base
        if not offers:
            offers["default"] = {
                "id": "default",
                "name": f"Offerta Base {op_name}",
                "description": "Parametri standard",
            }
            if commodity == "energy":
                offers["default"].update(DEFAULT_OFFER_VALUES)
            elif commodity == "water":
                offers["default"].update(DEFAULT_WATER_VALUES)

        operators[op_id] = {
            "id": op_id,
            "name": op_name,
            "offers": offers,
        }

    return operators


async def async_load_operators_and_offers(
    hass: Any, commodity: str = "energy", base_dir: Path | None = None
) -> dict[str, dict[str, Any]]:
    """Carica operatori e offerte in modo asincrono nell'executor senza bloccare l'event loop."""
    return await hass.async_add_executor_job(
        load_operators_and_offers, commodity, base_dir
    )
