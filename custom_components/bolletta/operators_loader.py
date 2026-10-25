"""Modulo per il caricamento dinamico di operatori e offerte da file JSON e XML."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

_LOGGER = logging.getLogger(__name__)

DEFAULT_OFFER_VALUES = {
    "ccl": 0.0150,
    "pcv": 90.00,
    "dispbt": 1.107,
    "pd": 0.0018,
    "pd_forfettario": 0.0,
    "include_losses": True,
    "accisa": 0.0227,
    "iva": 10.0,
}


def _parse_xml_offer(file_path: Path) -> dict[str, Any]:
    """Estrae i dati di un'offerta da un file XML."""
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

    return {
        "id": offer_id,
        "name": name,
        "description": desc,
        "ccl": get_float("ccl", DEFAULT_OFFER_VALUES["ccl"]),
        "pcv": get_float("pcv", DEFAULT_OFFER_VALUES["pcv"]),
        "dispbt": get_float("dispbt", DEFAULT_OFFER_VALUES["dispbt"]),
        "pd": get_float("pd", DEFAULT_OFFER_VALUES["pd"]),
        "pd_forfettario": get_float("pd_forfettario", DEFAULT_OFFER_VALUES["pd_forfettario"]),
        "include_losses": get_bool("include_losses", DEFAULT_OFFER_VALUES["include_losses"]),
        "accisa": get_float("accisa", DEFAULT_OFFER_VALUES["accisa"]),
        "iva": get_float("iva", DEFAULT_OFFER_VALUES["iva"]),
    }


def _parse_json_offer(file_path: Path) -> dict[str, Any]:
    """Estrae i dati di un'offerta da un file JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    offer_id = data.get("id", file_path.stem)
    name = data.get("name", offer_id.replace("_", " ").title())
    desc = data.get("description", "")

    return {
        "id": offer_id,
        "name": name,
        "description": desc,
        "ccl": float(data.get("ccl", DEFAULT_OFFER_VALUES["ccl"])),
        "pcv": float(data.get("pcv", DEFAULT_OFFER_VALUES["pcv"])),
        "dispbt": float(data.get("dispbt", DEFAULT_OFFER_VALUES["dispbt"])),
        "pd": float(data.get("pd", DEFAULT_OFFER_VALUES["pd"])),
        "pd_forfettario": float(data.get("pd_forfettario", DEFAULT_OFFER_VALUES["pd_forfettario"])),
        "include_losses": bool(data.get("include_losses", DEFAULT_OFFER_VALUES["include_losses"])),
        "accisa": float(data.get("accisa", DEFAULT_OFFER_VALUES["accisa"])),
        "iva": float(data.get("iva", DEFAULT_OFFER_VALUES["iva"])),
    }


def load_operators_and_offers(base_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Effettua la scansione della cartella operators e carica tutti gli operatori e le relative offerte."""
    if base_dir is None:
        base_dir = Path(__file__).parent / "operators"

    operators: dict[str, dict[str, Any]] = {}

    if not base_dir.exists():
        _LOGGER.warning("Cartella operatori %s non trovata", base_dir)
        return operators

    for op_dir in sorted(base_dir.iterdir()):
        if not op_dir.is_dir() or op_dir.name.startswith("."):
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
                    offer_data = _parse_json_offer(file)
                    offers[offer_data["id"]] = offer_data
                elif file.suffix.lower() == ".xml":
                    offer_data = _parse_xml_offer(file)
                    offers[offer_data["id"]] = offer_data
            except Exception as err:
                _LOGGER.error("Errore nel parsing dell'offerta %s: %s", file, err)

        # Se non ci sono offerte, crea un'offerta base
        if not offers:
            offers["default"] = {
                "id": "default",
                "name": f"Offerta Base {op_name}",
                "description": "Parametri standard",
                **DEFAULT_OFFER_VALUES,
            }

        operators[op_id] = {
            "id": op_id,
            "name": op_name,
            "offers": offers,
        }

    return operators
