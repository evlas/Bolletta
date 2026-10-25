"""Motore di calcolo tariffe e fasce orarie italiane (F1, F2, F3)."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Literal


def compute_easter(year: int) -> date:
    """Calcola la data della domenica di Pasqua (algoritmo anonimo di Meeus/Jones/Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def is_italian_holiday(target_date: date) -> bool:
    """Verifica se una data è un giorno festivo nazionale italiano."""
    year = target_date.year
    month = target_date.month
    day = target_date.day

    # Festività fisse
    fixed_holidays = {
        (1, 1),   # Capodanno
        (1, 6),   # Epifania
        (4, 25),  # Liberazione
        (5, 1),   # Festa del Lavoro
        (6, 2),   # Festa della Repubblica
        (8, 15),  # Ferragosto
        (11, 1),  # Ognissanti
        (12, 8),  # Immacolata Concezione
        (12, 25), # Natale
        (12, 26), # Santo Stefano
    }
    if (month, day) in fixed_holidays:
        return True

    # Pasquetta (Lunedì dell'Angelo)
    easter_sunday = compute_easter(year)
    easter_monday = easter_sunday + timedelta(days=1)
    if target_date == easter_monday:
        return True

    return False


def get_fascia_oraria(dt: datetime | None = None) -> Literal["F1", "F2", "F3"]:
    """Restituisce la fascia oraria ARERA (F1, F2, F3) per il momento indicato.
    
    Regole ARERA:
    - F1 (Ore di punta): Lunedì-Venerdì dalle 08:00 alle 19:00 (esclusi festivi)
    - F2 (Ore intermedie): Lunedì-Venerdì dalle 07:00 alle 08:00 e dalle 19:00 alle 23:00;
                          Sabato dalle 07:00 alle 23:00 (esclusi festivi)
    - F3 (Ore fuori punta): Lunedì-Sabato dalle 23:00 alle 07:00 del mattino successivo;
                           Domeniche e festività nazionali tutto il giorno.
    """
    if dt is None:
        dt = datetime.now()

    # Domenica o Festività Nazionale -> sempre F3
    if dt.weekday() == 6 or is_italian_holiday(dt.date()):
        return "F3"

    hour = dt.hour

    # Sabato
    if dt.weekday() == 5:
        if 7 <= hour < 23:
            return "F2"
        return "F3"

    # Lunedì - Venerdì
    if 8 <= hour < 19:
        return "F1"
    if hour == 7 or (19 <= hour < 23):
        return "F2"
    return "F3"


def compute_prezzo_energia(
    pun: float,
    ccl: float,
    pd: float,
    pd_forfettario: float,
    s3: float,
    uc3: float,
    uc6: float,
    asos: float,
    arim: float,
    accisa: float,
    iva_percent: float,
    include_losses: bool = True,
    decimals: int = 6,
) -> float:
    """Calcola il prezzo unitario al kWh secondo la formula del fornitore:
    ((PUN + perdite + ccl + pd + pd_forfettario + s3 + uc3 + uc6 + asos + arim + accisa) * (1 + iva/100))
    """
    pdr = (pun * 0.10) if include_losses else 0.0
    costo_base = (
        pun
        + pdr
        + ccl
        + pd
        + pd_forfettario
        + s3
        + uc3
        + uc6
        + asos
        + arim
        + accisa
    )
    totale = costo_base * (1.0 + (iva_percent / 100.0))
    return round(totale, decimals)


def compute_prezzo_fisso_giornaliero(
    pcv: float,
    dispbt: float,
    qf_s1: float,
    qp_s2: float,
    uc6_qp: float,
    power_kw: float,
    iva_percent: float,
    decimals: int = 6,
) -> float:
    """Calcola la quota fissa giornaliera:
    ((PCV + DispBT + QF + QP*kW + UC6_QP*kW) * (1 + iva/100)) / 365
    """
    costo_annuo = pcv + dispbt + qf_s1 + (qp_s2 * power_kw) + (uc6_qp * power_kw)
    totale_giornaliero = (costo_annuo * (1.0 + (iva_percent / 100.0))) / 365.0
    return round(totale_giornaliero, decimals)
