#  Integrazione Bolletta Elettrica per Home Assistant

Integrazione personalizzata (compatibile **HACS**) per il calcolo trasparente e in tempo reale del costo dell'energia elettrica e delle quote fisse della bolletta italiana in Home Assistant.

---

## ⚡ Caratteristiche Principali

- **Configurazione 100% da Interfaccia Grafica (Config Flow & Options Flow)**: aggiungi e modifica tariffe, potenza del contatore e spread direttamente dalla UI senza mai riavviare Home Assistant.
- **Preset Operatori Integrati**:
  - **Engie** (Energia Chiara / Relax: spread CCL, PCV, DispBT, PD, perdite di rete 10%).
  - **Octopus Energy** (Octopus Flex / Fissa: spread alfa, PCV 8€/mese, perdite di rete 10%).
  - **Dolomiti Energia** (Mitica / Flex: spread, PCV 9.50€/mese, perdite di rete 10%).
  - **Personalizzato**: per qualsiasi altro operatore (A2A, Nen, Sorgenia, Enel, Eni Plenitude, Iren, ecc.).
- **Multi-Istanza**: puoi configurare più contratti contemporaneamente (es. prima e seconda casa, oppure confrontare due fornitori diversi per simulare i costi).
- **Integrazione con Sensori PUN esistenti**: selettore nativo di entità per agganciare i sensori PUN (es. da `pun_sensor` o altre integrazioni HACS) per F0, F1, F2, F3.
- **Supporto Integrazione ARERA**:
  - Rileva e si collega automaticamente alle entità generate dall'integrazione dedicata **ARERA Tariffe Luce** (`sensor.arera_*`).
  - Se l'integrazione ARERA non è installata, utilizza comunque valori ufficiali ARERA di fallback senza bloccare il calcolo.
- **Fasce Orarie Italiane Dinamiche (F1, F2, F3)**:
  - Calcola in tempo reale la fascia attiva rispettando il calendario nazionale italiano e la Pasquetta (algoritmo astronomico integrato).
  - Espone il sensore **Prezzo Unitario Attuale** ideale per la **Dashboard Energia** e per le automazioni di carichi ed elettrodomestici.

---

## 📦 Struttura del Progetto

```
Bolletta/
├── custom_components/
│   └── bolletta/                  # Integrazione principale Bolletta
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── config_flow.py
│       ├── sensor.py
│       ├── tariffs.py             # Motore di calcolo & fasce orarie italiane
│       └── translations/
│           ├── it.json
│           └── en.json
├── hacs.json
├── engie.yaml                     # Vecchio package YAML di riferimento
└── README.md
```

---

## 🚀 Installazione

### Metodo 1: Tramite HACS (Consigliato)
1. Apri **HACS** in Home Assistant -> *Integrazioni*.
2. Clicca sui tre puntini in alto a destra -> *Repository personalizzati*.
3. Inserisci l'URL del repository GitHub `Bolletta` e seleziona la categoria **Integrazione**.
4. Clicca su **Scarica** e riavvia Home Assistant.

### Metodo 2: Manuale
1. Copia la cartella `custom_components/bolletta` all'interno della cartella `custom_components/` del tuo Home Assistant.
2. Riavvia Home Assistant.

---

## ⚙️ Configurazione

1. Vai su **Impostazioni** -> **Dispositivi e Servizi** -> **Aggiungi Integrazione**.
2. Cerca **Bolletta Elettrica**.
3. **Passo 1**: Inserisci il nome dell'istanza (es. *Bolletta Engie*), seleziona l'operatore (**Engie**, **Octopus Energy**, **Dolomiti Energia** o **Personalizzato**) e la potenza impegnata (es. *3 kW*, *4.5 kW*, *6 kW*).
4. **Passo 2**: Seleziona i tuoi sensori PUN già presenti in Home Assistant (es. generati da `pun_sensor`).
5. **Passo 3**: Verifica i parametri contrattuali (troverai già precompilati quelli tipici dell'operatore scelto).
6. **Passo 4**: Se l'integrazione ARERA è attiva, i sensori verranno agganciati automaticamente.

---

## 📊 Entità Create

Tutti i sensori sono raggruppati in un unico dispositivo (es. *Bolletta Engie*):

| Sensore | Descrizione | Unità |
| :--- | :--- | :--- |
| `sensor.<istanza>_prezzo_unitario_f0` | Prezzo finito Monorario F0 | €/kWh |
| `sensor.<istanza>_prezzo_unitario_f1` | Prezzo finito Fascia F1 (Ore di punta) | €/kWh |
| `sensor.<istanza>_prezzo_unitario_f2` | Prezzo finito Fascia F2 (Intermedie) | €/kWh |
| `sensor.<istanza>_prezzo_unitario_f3` | Prezzo finito Fascia F3 (Fuori punta) | €/kWh |
| `sensor.<istanza>_prezzo_unitario_attuale` | **Prezzo in tempo reale** della fascia attiva | €/kWh |
| `sensor.<istanza>_fascia_attuale` | Fascia oraria attuale (**F1**, **F2**, **F3**) | - |
| `sensor.<istanza>_prezzo_fisso_giornaliero` | Quota fissa giornaliera (PCV + ARERA + DispBT + Potenza) | €/giorno |
| `sensor.<istanza>_costo_fisso_mensile` | Quota fissa media mensile | €/mese |

---

## ⚡ Formule di Calcolo

### Prezzo Unitario Energia (€/kWh):
$$\text{Prezzo} = \left(\text{PUN} + \text{PDR}_{10\%} + \text{CCL} + \text{PD} + \text{PD}_{\text{forf}} + s_3 + \text{UC}_3 + \text{UC}_{6\text{qe}} + \text{ASOS} + \text{ARIM} + \text{Accisa}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)$$

### Quota Fissa Giornaliera (€/giorno):
$$\text{Quota Fissa} = \frac{\left(\text{PCV} + \text{DispBT} + s_1 + s_2 \cdot \text{kW} + \text{UC}_{6\text{qp}} \cdot \text{kW}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)}{365}$$
