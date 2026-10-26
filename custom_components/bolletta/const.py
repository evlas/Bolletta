"""Costanti per l'integrazione Bolletta Elettrica."""

DOMAIN = "bolletta"

# Tipi di fornitura / Commodity
CONF_COMMODITY = "commodity"
COMMODITY_ENERGY = "energy"
COMMODITY_WATER = "water"
COMMODITY_GAS = "gas"

COMMODITIES = {
    COMMODITY_ENERGY: "Energia Elettrica (Luce)",
    COMMODITY_WATER: "Acqua (Servizio Idrico)",
    COMMODITY_GAS: "Gas Naturale",
}

# Operatori supportati energia
OPERATOR_ENGIE = "engie"
OPERATOR_OCTOPUS = "octopus"
OPERATOR_DOLOMITI = "dolomiti"
OPERATOR_CUSTOM = "custom"

OPERATORS = {
    OPERATOR_ENGIE: "Engie",
    OPERATOR_OCTOPUS: "Octopus Energy",
    OPERATOR_DOLOMITI: "Dolomiti Energia",
    OPERATOR_CUSTOM: "Personalizzato",
}

# Parametri contrattuali predefiniti per operatore
# Parametri contrattuali predefiniti per operatore
OPERATOR_PRESETS = {
    OPERATOR_ENGIE: {
        "name": "Engie",
        "ccl": 0.0152,           # Contributo al consumo / spread (€/kWh)
        "pcv": 69.88,            # Commercializzazione venditore (€/anno)
        "pd": 0.0018,            # Dispacciamento (€/kWh)
        "pd_forfettario": 0.0000,# Dispacciamento forfettario (€/kWh)
        "include_losses": True,  # Perdite di rete 10% su PUN
        "accisa": 0.0227,        # Accisa (€/kWh)
        "iva": 10.0,             # IVA (%)
    },
    OPERATOR_OCTOPUS: {
        "name": "Octopus Energy",
        "ccl": 0.01628,          # Spread alfa (€/kWh)
        "pcv": 96.00,            # Commercializzazione fissa (8 €/mese) (€/anno)
        "pd": 0.0018,
        "pd_forfettario": 0.0000,
        "include_losses": True,
        "accisa": 0.0227,
        "iva": 10.0,
    },
    OPERATOR_DOLOMITI: {
        "name": "Dolomiti Energia",
        "ccl": 0.0175,           # Spread corrispettivo luce (€/kWh)
        "pcv": 114.00,           # Commercializzazione venditore (9.5 €/mese) (€/anno)
        "pd": 0.0018,
        "pd_forfettario": 0.0000,
        "include_losses": True,
        "accisa": 0.0227,
        "iva": 10.0,
    },
    OPERATOR_CUSTOM: {
        "name": "Personalizzato",
        "ccl": 0.0150,
        "pcv": 90.00,
        "pd": 0.0018,
        "pd_forfettario": 0.0000,
        "include_losses": True,
        "accisa": 0.0227,
        "iva": 10.0,
    },
}

# Chiavi di configurazione
CONF_OPERATOR = "operator"
CONF_OFFER = "offer"
CONF_POWER_KW = "power_kw"
CONF_USE_MULTIORARIO = "use_multiorario"

# Sensori PUN
CONF_PUN_F0 = "pun_f0"
CONF_PUN_F1 = "pun_f1"
CONF_PUN_F2 = "pun_f2"
CONF_PUN_F3 = "pun_f3"

# Parametri contrattuali
CONF_CCL = "ccl"
CONF_PCV = "pcv"
CONF_PD = "pd"
CONF_PD_FORFETTARIO = "pd_forfettario"
CONF_INCLUDE_LOSSES = "include_losses"
CONF_ACCISA = "accisa"
CONF_IVA = "iva"

# Formule di calcolo personalizzabili
CONF_FORMULA_ENERGIA = "formula_energia"
CONF_FORMULA_QUOTA_FISSA = "formula_quota_fissa"

DEFAULT_FORMULA_ENERGIA = (
    "((pun * (1.10 if include_losses else 1.0) + ccl + pd + pd_forfettario "
    "+ s3 + uc3 + uc6_qe + asos + arim + accisa) * (1 + iva / 100))"
)
DEFAULT_FORMULA_QUOTA_FISSA = (
    "(((pcv + dispbt + s1 + (s2 + uc6_qp) * power_kw) * (1 + iva / 100)) / 365)"
)

# Sensori ARERA (opzionali o auto-rilevati)
CONF_ARERA_S1 = "arera_s1"
CONF_ARERA_S2 = "arera_s2"
CONF_ARERA_S3 = "arera_s3"
CONF_ARERA_UC3 = "arera_uc3"
CONF_ARERA_UC6_QE = "arera_uc6_qe"
CONF_ARERA_UC6_QP = "arera_uc6_qp"
CONF_ARERA_ASOS = "arera_asos"
CONF_ARERA_ARIM = "arera_arim"
CONF_ARERA_DISPBT = "arera_dispbt"

DEFAULT_POWER_KW = 3.0
POWER_PRESETS = [1.5, 3.0, 4.5, 6.0, 10.0, 15.0]

# Valori di fallback per ARERA se non sono disponibili sensori dedicati
FALLBACK_ARERA = {
    "s1": 23.04,
    "s2": 23.52,
    "s3": 0.0119,
    "uc3": 0.00276,
    "uc6_qe": 0.00007,
    "uc6_qp": 0.1988,
    "asos": 0.028657,
    "arim": 0.001638,
    "dispbt": 1.107,
}

# Parametri e chiavi per la bolletta Acqua (Servizio Idrico)
CONF_WATER_SENSOR = "water_sensor"
CONF_QF_IDRICO = "qf_idrico"
CONF_QF_FOGNATURA = "qf_fognatura"
CONF_QF_DEPURAZIONE = "qf_depurazione"
CONF_USA_FOGNATURA_DEPURAZIONE = "usa_fognatura_depurazione"
CONF_USA_FOGNATURA = "usa_fognatura"
CONF_USA_DEPURAZIONE = "usa_depurazione"
CONF_S1 = "s1"
CONF_S2 = "s2"
CONF_S3 = "s3"
CONF_S4 = "s4"
CONF_T_AGEVOLATA = "t_agevolata"
CONF_T_BASE = "t_base"
CONF_T_ECC1 = "t_ecc1"
CONF_T_ECC2 = "t_ecc2"
CONF_T_ECC3 = "t_ecc3"
CONF_T_FOGNATURA = "t_fognatura"
CONF_T_DEPURAZIONE = "t_depurazione"
CONF_UI1 = "ui1"
CONF_UI2 = "ui2"
CONF_UI3 = "ui3"
CONF_WATER_ANNUAL_BASELINE = "water_annual_baseline"

DEFAULT_WATER_VALUES = {
    CONF_QF_IDRICO: 33.60,
    CONF_QF_FOGNATURA: 4.90,
    CONF_QF_DEPURAZIONE: 14.70,
    CONF_USA_FOGNATURA_DEPURAZIONE: True,
    CONF_USA_FOGNATURA: True,
    CONF_USA_DEPURAZIONE: True,
    CONF_WATER_ANNUAL_BASELINE: 0.0,
    CONF_S1: 55.0,
    CONF_S2: 108.0,
    CONF_S3: 162.0,
    CONF_S4: 216.0,
    CONF_T_AGEVOLATA: 0.4445,
    CONF_T_BASE: 1.2583,
    CONF_T_ECC1: 1.8874,
    CONF_T_ECC2: 2.5166,
    CONF_T_ECC3: 3.7748,
    CONF_T_FOGNATURA: 0.3525,
    CONF_T_DEPURAZIONE: 0.7049,
    CONF_UI1: 0.004,
    CONF_UI2: 0.009,
    CONF_UI3: 0.005,
    CONF_IVA: 10.0,
}

