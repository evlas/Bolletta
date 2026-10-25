"""Costanti per l'integrazione Bolletta Elettrica."""

DOMAIN = "bolletta"

# Operatori supportati
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
OPERATOR_PRESETS = {
    OPERATOR_ENGIE: {
        "name": "Engie",
        "ccl": 0.0152,           # Contributo al consumo / spread (€/kWh)
        "pcv": 69.88,            # Commercializzazione venditore (€/anno)
        "dispbt": -10.77,        # DispBT (€/anno)
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
        "dispbt": -10.77,
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
        "dispbt": -10.77,
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
        "dispbt": -10.77,
        "pd": 0.0018,
        "pd_forfettario": 0.0000,
        "include_losses": True,
        "accisa": 0.0227,
        "iva": 10.0,
    },
}

# Chiavi di configurazione
CONF_OPERATOR = "operator"
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
CONF_DISPBT = "dispbt"
CONF_PD = "pd"
CONF_PD_FORFETTARIO = "pd_forfettario"
CONF_INCLUDE_LOSSES = "include_losses"
CONF_ACCISA = "accisa"
CONF_IVA = "iva"

# Sensori ARERA (opzionali o auto-rilevati)
CONF_ARERA_S1 = "arera_s1"
CONF_ARERA_S2 = "arera_s2"
CONF_ARERA_S3 = "arera_s3"
CONF_ARERA_UC3 = "arera_uc3"
CONF_ARERA_UC6_QE = "arera_uc6_qe"
CONF_ARERA_UC6_QP = "arera_uc6_qp"
CONF_ARERA_ASOS = "arera_asos"
CONF_ARERA_ARIM = "arera_arim"

DEFAULT_POWER_KW = 3.0
POWER_PRESETS = [1.5, 3.0, 4.5, 6.0, 10.0, 15.0]

# Valori di fallback per ARERA se non sono disponibili sensori dedicati
FALLBACK_ARERA = {
    "s1": 24.40,
    "s2": 23.50,
    "s3": 0.0135,
    "uc3": 0.0016,
    "uc6_qe": 0.0001,
    "uc6_qp": 0.0000,
    "asos": 0.0345,
    "arim": 0.0090,
}
