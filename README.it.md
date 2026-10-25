# Bolletta Elettrica - Integrazione Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Bolletta?color=blue&style=flat-square)](https://github.com/evlas/Bolletta/releases)
[![Hassfest](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.8%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *[English version](README.md) | Versione in italiano*

Integrazione professionale per **Home Assistant** per calcolare in modo trasparente e in tempo reale il costo dell'energia elettrica e le quote fisse della bolletta per i contratti di fornitura domestica in Italia.

Si collega facilmente ai sensori **PUN** (Prezzo Unico Nazionale) esistenti e alle componenti tariffarie regolate **ARERA**, supportando sia tariffe monorarie (F0) che multiorarie a fasce (F1, F2, F3).

---

## 🚀 Caratteristiche Principali

- **Architettura Modulare a Operatori e Offerte (JSON & XML)**:
  - Ogni operatore ha una propria cartella in `custom_components/bolletta/operators/<operatore>/`.
  - Ogni offerta commerciale (es. indicizzata PUN, prezzo fisso, formule custom) è un file `.json` o `.xml` indipendente.
  - È facilissimo aggiungere nuovi operatori e offerte senza toccare il codice Python dell'integrazione!
  - **Preset Inclusi**: **Engie** (*Energia Chiara*, *Energia Relax*), **Octopus Energy** (*Octopus Flex*, *Octopus Fissa 12M*), **Dolomiti Energia** (*Mitica Web / Flex*), **Operatore Personalizzato** (esempi JSON e XML pronti all'uso).
- **Motore di Formule Matematiche Dinamiche**:
  - Ogni offerta definisce le proprie formule matematiche per il prezzo dell'energia (`formula_energia`) e per la quota fissa (`formula_quota_fissa`).
  - Supporta offerte a prezzo indicizzato PUN, offerte a prezzo fisso al kWh, sconti percentuali, scaglioni o formule contrattuali proprietarie.
- **Disaccoppiamento DispBT (Agganciato ad ARERA)**:
  - `DispBT` non è più un parametro statico del venditore, ma una componente regolata ARERA acquisita dinamicamente dal sensore `sensor.arera_dispbt` dell'integrazione compagna.
- **Configurazione 100% da WebUI (Config Flow & Options Flow)**: Selezione guidata dell'operatore e dell'offerta da *Impostazioni -> Dispositivi e Servizi*, con possibilità di modificare i parametri in qualsiasi momento.
- **Supporto Multi-Istanza**: Puoi aggiungere più contratti contemporaneamente (es. prima casa, seconda casa, o confrontare due operatori/offerte in tempo reale).
- **Fasce Orarie Italiane Dinamiche (F1, F2, F3)**:
  - Rileva automaticamente e in tempo reale la fascia attiva in base alle regole ARERA, giorno della settimana, orario e festività nazionali italiane (inclusa la Pasquetta calcolata con algoritmo astronomico).
  - Espone l'entità `sensor.<istanza>_prezzo_unitario_attuale`, che riflette all'istante il prezzo della fascia in vigore.
- **Integrazione con la Dashboard Energia di Home Assistant**:
  - Sensori configurati con `device_class: monetary`, `state_class: measurement` e valuta `EUR/kWh`.
  - Pronti per essere inseriti direttamente come tariffa dinamica nella Dashboard Energia ufficiale.
- **Collegamento Diretto con i Sensori PUN**: Selettore grafico nativo per agganciare i sensori PUN già presenti in Home Assistant (es. generati da HACS `pun_sensor`).
- **Integrazione con ARERA**:
  - Rileva e si aggancia automaticamente alle entità regolate dell'integrazione compagna **ARERA Tariffe Luce** (`sensor.arera_*`), incluso `sensor.arera_dispbt`.
  - Include valori ufficiali ARERA di fallback se l'integrazione compagna non è presente.
- **Calcolo Completo dei Costi Fissi**:
  - Calcola la quota fissa giornaliera (`EUR/day`) e la stima mensile (`EUR/month`) combinando PCV, DispBT, quota potenza impegnata, quota fissa trasporto e IVA.

---

## 📦 Installazione

### Metodo 1: Tramite HACS (Consigliato)

1. Apri **HACS** in Home Assistant.
2. Vai su **Integrazioni** -> Menu tre puntini in alto a destra -> **Repository personalizzati**.
3. Incolla `https://github.com/evlas/Bolletta.git`, seleziona la categoria **Integrazione** e clicca **Aggiungi**.
4. Cerca **Bolletta Elettrica** e clicca su **Scarica**.
5. Riavvia Home Assistant.

### Metodo 2: Installazione Manuale

1. Scarica la cartella `custom_components/bolletta`.
2. Copiala nella directory `custom_components/` della tua installazione di Home Assistant:
   ```
   /config/custom_components/bolletta/
   ```
3. Riavvia Home Assistant.

---

## ⚙️ Configurazione

1. Nella WebUI di Home Assistant, vai su **Impostazioni** -> **Dispositivi e Servizi**.
2. Clicca su **Aggiungi Integrazione** in basso a destra.
3. Cerca **Bolletta Elettrica**.
4. Segui la procedura guidata a passi:
   - **Passo 1: Generale**: Assegna un nome all'istanza (es. *Bolletta Engie*), scegli l'operatore tra quelli disponibili nella cartella `operators/`, seleziona la potenza impegnata (es. `3.0 kW`, `4.5 kW`, `6.0 kW`) e abilita la tariffa multioraria.
   - **Passo 2: Offerta Commerciale**: Seleziona l'offerta specifica del venditore (es. *Energia Chiara*, *Octopus Flex*, *Prezzo Fisso*, ecc.). I parametri e le formule matematiche vengono precaricati automaticamente dal file corrispondente.
   - **Passo 3: Sensori PUN**: Seleziona i tuoi sensori PUN esistenti in Home Assistant (F0 se monorario, oppure F1, F2, F3 se multiorario).
   - **Passo 4: Parametri Contrattuali**: Verifica o personalizza i parametri del venditore (Spread/CCL, PCV, Dispacciamento PD, Accisa, IVA, ecc.).
   - **Passo 5: Collegamento ARERA**: Conferma o seleziona le entità ARERA rilevate automaticamente (incluso `sensor.arera_dispbt`).

> [!TIP]
> Puoi modificare qualsiasi parametro contrattuale, potenza impegnata, spread o formula in ogni momento cliccando su **Configura / Opzioni** sulla scheda dell'integrazione senza dover riavviare.

---

## 🛠️ Come Creare Operatori e Offerte Personalizzate

L'integrazione Bolletta utilizza un'architettura completamente modulare e scalabile. Per aggiungere un nuovo fornitore o una nuova tariffa non occorre modificare il codice Python: basta aggiungere una cartella e i rispettivi file `.json` o `.xml`.

### 1. Struttura delle Directory

Tutti gli operatori si trovano in:
```text
custom_components/bolletta/operators/
├── <id_operatore>/
│   ├── operator.json           <-- Metadati dell'operatore (obbligatorio)
│   ├── offerta_1.json          <-- Offerta in JSON (consigliato)
│   ├── offerta_2.xml           <-- Offerta in XML (supportato)
│   └── ...
```

### 2. File Metadati Operatore (`operator.json` o `operator.xml`)

Crea il file `operator.json` nella cartella del fornitore:
```json
{
  "id": "mio_operatore",
  "name": "Mio Fornitore Luce",
  "description": "Descrizione del fornitore (es. Mercato Libero)"
}
```

Oppure in formato XML (`operator.xml`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<operator>
  <id>mio_operatore</id>
  <name>Mio Fornitore Luce</name>
  <description>Descrizione del fornitore</description>
</operator>
```

### 3. File delle Offerte Commerciali

Ogni file `.json` o `.xml` presente nella cartella dell'operatore (diverso da `operator.*`) rappresenta un'offerta selezionabile nel Config Flow.

#### Parametri Standard di un'Offerta:
- `id`: Identificativo univoco dell'offerta (es. `mia_offerta_flex`).
- `name`: Nome leggibile mostrato nel menu a tendina (es. `Mio Fornitore Flex (PUN + Spread)`).
- `description`: Breve descrizione della tariffa.
- `ccl`: Spread o contributo al consumo del venditore in €/kWh (es. `0.015`).
- `pcv`: Quota fissa di commercializzazione e vendita del fornitore in €/anno (es. `72.00`).
- `pd`: Dispacciamento componente mercato all'ingrosso in €/kWh (es. `0.0018`).
- `pd_forfettario`: Dispacciamento forfettario addizionale in €/kWh (es. `0.0`).
- `include_losses`: `true` per applicare il 10% di perdite di rete al PUN, `false` altrimenti.
- `accisa`: Imposta erariale di consumo in €/kWh (default `0.0227`).
- `iva`: Percentuale IVA (default `10.0`).
- `formula_energia`: Espressione matematica personalizzata per il calcolo del prezzo al kWh (€/kWh finito).
- `formula_quota_fissa`: Espressione matematica personalizzata per il calcolo della quota fissa annua (€/anno prima di dividere per 365).

> [!NOTE]
> `dispbt` **non** deve essere inserito nei file delle offerte: è una componente regolata ARERA recuperata automaticamente in tempo reale dal sensore `sensor.arera_dispbt`.

---

### 4. Il Motore delle Formule Matematiche

Le formule possono contenere qualsiasi operatore matematico standard (`+`, `-`, `*`, `/`, `**`, parentesi, costanti numeriche e costrutti condizionali `x if c else y`).

#### Variabili disponibili nella formula `formula_energia`:
| Variabile | Descrizione |
| :--- | :--- |
| `pun` | Valore del Prezzo Unico Nazionale (€/kWh) della fascia oraria considerata |
| `ccl` | Spread o contributo al consumo dell'operatore (€/kWh) |
| `pd` | Dispacciamento variabile (€/kWh) |
| `pd_forfettario` | Dispacciamento forfettario (€/kWh) |
| `include_losses` | Valore booleano (se le perdite di rete 10% sono abilitate) |
| `accisa` | Accisa erariale (€/kWh) |
| `iva` | Aliquota IVA in percentuale (es. 10.0) |
| `s3` | ARERA quota energia trasporto e misura $\sigma_3$ (€/kWh) |
| `uc3` | ARERA perequazione trasporto $\text{UC}_3$ (€/kWh) |
| `uc6_qe` | ARERA qualità servizio quota energia $\text{UC}_{6\text{qe}}$ (€/kWh) |
| `asos` | ARERA oneri generali rinnovabili $\text{ASOS}$ (€/kWh) |
| `arim` | ARERA altri oneri di sistema $\text{ARIM}$ (€/kWh) |
| *custom* | Qualsiasi parametro addizionale definito nel file JSON/XML dell'offerta |

#### Variabili disponibili nella formula `formula_quota_fissa`:
| Variabile | Descrizione |
| :--- | :--- |
| `pcv` | Quota fissa di commercializzazione del venditore (€/anno) |
| `dispbt` | Componente regolata ARERA dal sensore `sensor.arera_dispbt` (€/anno) |
| `s1` | ARERA quota fissa trasporto $\sigma_1$ (€/anno) |
| `s2` | ARERA quota potenza trasporto $\sigma_2$ (€/kW/anno) |
| `uc6_qp` | ARERA quota potenza qualità $\text{UC}_{6\text{qp}}$ (€/kW/anno) |
| `power_kw` | Potenza impegnata del contatore in kW (es. 3.0, 4.5, 6.0) |
| `iva` | Aliquota IVA in percentuale (es. 10.0) |
| *custom* | Qualsiasi parametro addizionale definito nel file JSON/XML dell'offerta |

---

### 5. Esempi Completi

#### Esempio 1: Offerta Indicizzata al PUN (`offerta_indicizzata.json`)
```json
{
  "id": "offerta_indicizzata",
  "name": "Luce Dinamica (PUN + Spread)",
  "description": "Offerta a prezzo variabile indicizzato al PUN mensile",
  "ccl": 0.015,
  "pcv": 72.0,
  "pd": 0.0018,
  "pd_forfettario": 0.0,
  "include_losses": true,
  "accisa": 0.0227,
  "iva": 10.0,
  "formula_energia": "((pun * (1.10 if include_losses else 1.0) + ccl + pd + pd_forfettario + s3 + uc3 + uc6_qe + asos + arim + accisa) * (1 + iva / 100))",
  "formula_quota_fissa": "((pcv + dispbt + s1 + (s2 + uc6_qp) * power_kw) * (1 + iva / 100))"
}
```

#### Esempio 2: Offerta a Prezzo Fisso per 12 Mesi (`offerta_fissa.json`)
Offerta non indicizzata al PUN ma con prezzo costante bloccato al kWh (`prezzo_fisso_kwh`):
```json
{
  "id": "offerta_prezzo_fisso_12m",
  "name": "Luce Bloccata 12 Mesi (Prezzo Fisso)",
  "description": "Prezzo fisso bloccato della materia prima energia per 12 mesi",
  "prezzo_fisso_kwh": 0.125,
  "ccl": 0.0,
  "pcv": 84.0,
  "pd": 0.0018,
  "pd_forfettario": 0.0,
  "include_losses": false,
  "accisa": 0.0227,
  "iva": 10.0,
  "formula_energia": "((prezzo_fisso_kwh + pd + pd_forfettario + s3 + uc3 + uc6_qe + asos + arim + accisa) * (1 + iva / 100))",
  "formula_quota_fissa": "((pcv + dispbt + s1 + (s2 + uc6_qp) * power_kw) * (1 + iva / 100))"
}
```

#### Esempio 3: Offerta in Formato XML (`offerta_custom.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<offer>
  <id>offerta_xml_demo</id>
  <name>Tariffa XML Personalizzata</name>
  <description>Esempio di offerta con formula speciale caricata da XML</description>
  <ccl>0.012</ccl>
  <pcv>60.0</pcv>
  <pd>0.0018</pd>
  <pd_forfettario>0.0</pd_forfettario>
  <include_losses>true</include_losses>
  <accisa>0.0227</accisa>
  <iva>10.0</iva>
  <formula_energia>((pun * 1.10 + ccl + pd + s3 + uc3 + uc6_qe + asos + arim + accisa) * (1 + iva / 100))</formula_energia>
  <formula_quota_fissa>((pcv + dispbt + s1 + (s2 + uc6_qp) * power_kw) * (1 + iva / 100))</formula_quota_fissa>
</offer>
```

---

## 📊 Integrazione con la Dashboard Energia

Per associare il prezzo dinamico alla **Dashboard Energia** ufficiale di Home Assistant:

1. Vai su **Impostazioni** -> **Dashboard** -> **Energia**.
2. Nella sezione **Rete elettrica** -> **Consumo di rete**, modifica il tuo contatore di prelievo.
3. Alla voce *Prezzo dell'energia elettrica*, seleziona **Usa un'entità che traccia i costi totali o il prezzo**:
   - Seleziona `sensor.<tua_istanza>_prezzo_unitario_attuale`

---

## 🎛️ Esempio Scheda Lovelace

Esempio di dashboard Lovelace per monitorare tariffe attive e costi fissi:

```yaml
type: vertical-stack
title: Bolletta & Costo Energia
cards:
  - type: glance
    entities:
      - entity: sensor.bolletta_luce_fascia_attuale
        name: Fascia Attiva
      - entity: sensor.bolletta_luce_prezzo_unitario_attuale
        name: Prezzo Attuale
      - entity: sensor.bolletta_luce_prezzo_fisso_giornaliero
        name: Quota Fissa / Giorno
      - entity: sensor.bolletta_luce_costo_fisso_mensile
        name: Quota Fissa / Mese
  - type: entities
    title: Dettaglio Fasce Orarie
    entities:
      - entity: sensor.bolletta_luce_prezzo_unitario_f1
        name: Prezzo F1 (Picco)
      - entity: sensor.bolletta_luce_prezzo_unitario_f2
        name: Prezzo F2 (Intermedia)
      - entity: sensor.bolletta_luce_prezzo_unitario_f3
        name: Prezzo F3 (Fuori Picco)
      - entity: sensor.bolletta_luce_prezzo_unitario_f0
        name: Prezzo F0 (Monorario)
```

---

## ⚡ Formule Matematiche di Riferimento

### Prezzo Unitario dell'Energia (€/kWh):
$$\text{Prezzo} = \left(\text{PUN} \times (1 + \text{PDR}) + \text{CCL} + \text{PD} + \text{PD}_{\text{forf}} + s_3 + \text{UC}_3 + \text{UC}_{6\text{qe}} + \text{ASOS} + \text{ARIM} + \text{Accisa}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)$$

### Quota Fissa Giornaliera (€/giorno):
$$\text{Quota Fissa} = \frac{\left(\text{PCV} + \text{DispBT} + s_1 + s_2 \cdot \text{kW} + \text{UC}_{6\text{qp}} \cdot \text{kW}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)}{365}$$

---

## 📑 Entità Generate

| Entità | Descrizione | Unità | Classe |
| :--- | :--- | :--- | :--- |
| `sensor.<istanza>_prezzo_unitario_attuale` | **Prezzo in tempo reale** della fascia oraria attualmente attiva | EUR/kWh | measurement |
| `sensor.<istanza>_fascia_attuale` | Fascia oraria ARERA attiva (**F1**, **F2**, **F3**) | - | - |
| `sensor.<istanza>_prezzo_unitario_f0` | Prezzo finito tariffa Monoraria (F0) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f1` | Prezzo finito fascia Picco (F1) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f2` | Prezzo finito fascia Intermedia (F2) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f3` | Prezzo finito fascia Fuori Picco (F3) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_fisso_giornaliero` | Quota fissa giornaliera (PCV + ARERA + Potenza) | EUR/day | measurement |
| `sensor.<istanza>_costo_fisso_mensile` | Quota fissa media mensile | EUR/month | measurement |

---

## 🛠️ Integrazione Compagna ARERA

Per recuperare automaticamente e mantenere aggiornate le tariffe regolate di rete, gli oneri di sistema e la componente **DispBT** direttamente dai portali ufficiali ARERA, installa l'integrazione compagna:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 Licenza

Distribuito sotto licenza GNU General Public License v3.0 (GPLv3). Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
