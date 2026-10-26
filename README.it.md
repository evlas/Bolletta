# Bolletta (Luce, Acqua, Gas) - Integrazione Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Bolletta?color=blue&style=flat-square)](https://github.com/evlas/Bolletta/releases)
[![Hassfest](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.8%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *[English version](README.md) | Versione in italiano*

Integrazione professionale per **Home Assistant** per calcolare in modo trasparente e in tempo reale i costi e le quote fisse delle utenze domestiche in Italia (**Energia Elettrica**, **Acqua / Servizio Idrico Integrato** e **Gas Naturale**).

---

## 🚀 Caratteristiche Principali

- **Architettura Multi-Commodity (Luce, Acqua, Gas)**:
  - All'aggiunta dell'integrazione puoi scegliere il tipo di fornitura da monitorare:
    - ⚡ **Energia Elettrica (Luce)**: calcolo basato su PUN (monorario o multiorario F1, F2, F3), spread fornitore, perdite di rete, quote fisse PCV e integrazione automatica con i parametri regolati **ARERA**.
    - 💧 **Acqua / Servizio Idrico**: calcolo a scaglioni progressivi di consumo conforme al metodo tariffario **ARERA TICSI** (Delibera 665/2017/R/idr), quote fisse (acquedotto, fognatura, depurazione), tariffe reflue e componenti perequative ARERA ($UI_1$, $UI_2$, $UI_3$), con preset dedicati ad esempio per **Acea Ato 2 / Ato 5**.
    - 🔥 **Gas Naturale**: architettura predisposta con operatore e offerta personalizzabile (quota fissa annua, costo variabile al Smc, accise e addizionali regionali).
- **Architettura Modulare a Operatori e Offerte (JSON & XML)**:
  - Ogni tipologia di fornitura è organizzata in cartelle dedicate: `operators/energy/`, `operators/water/`, `operators/gas/`.
  - Ogni fornitore ha una propria sottocartella e ogni piano tariffario è un file `.json` o `.xml` indipendente.
  - È facilissimo aggiungere nuovi fornitori e offerte senza toccare il codice Python dell'integrazione!
  - **Preset Inclusi**:
    - **Luce**: **Engie** (*Energia Chiara*, *Energia Relax*, *Rinnovo Variabile*), **Octopus Energy** (*Octopus Flex*, *Octopus Fissa 12M*), **Dolomiti Energia** (*Mitica Web / Flex*), **Custom** (JSON e XML).
    - **Acqua**: **Acea Ato 2 / Ato 5** (*Domestico Residente* basato su TICSI), **Custom** (*Tariffa Idrica Personalizzata*).
    - **Gas**: **Custom** (*Tariffa Gas Personalizzata*).
- **Motore di Formule Matematiche Dinamiche (Luce)**:
  - Ogni offerta definisce le proprie formule matematiche per il prezzo dell'energia (`formula_energia`) e per la quota fissa (`formula_quota_fissa`).
  - Supporta offerte indicizzate PUN, a prezzo fisso al kWh, con sconti percentuali, scaglioni o formule proprietarie.
- **Disaccoppiamento DispBT (Agganciato ad ARERA)**:
  - `DispBT` non è un parametro fisso del venditore, ma una componente regolata ARERA acquisita dinamicamente dal sensore `sensor.arera_dispbt` dell'integrazione compagna.
- **Fasce Orarie Italiane Dinamiche (F1, F2, F3)**:
  - Rileva automaticamente e in tempo reale la fascia attiva in base alle regole ARERA, giorno della settimana, orario e festività nazionali italiane (inclusa la Pasquetta calcolata dinamicamente).
- **Configurazione 100% da WebUI (Config Flow & Options Flow)**: Selezione guidata della fornitura, dell'operatore e dell'offerta da *Impostazioni -> Dispositivi e Servizi*, con possibilità di modificare i parametri in qualsiasi momento.
- **Supporto Multi-Istanza**: Puoi aggiungere quante istanze desideri contemporaneamente (es. Contratto Luce Casa, Contratto Acqua, Contratto Luce Seconda Casa).

---

## 📦 Installazione

### Metodo 1: Tramite HACS (Consigliato)

1. Apri **HACS** in Home Assistant.
2. Vai su **Integrazioni** -> Menu tre puntini in alto a destra -> **Repository personalizzati**.
3. Incolla `https://github.com/evlas/Bolletta.git`, seleziona la categoria **Integrazione** e clicca **Aggiungi**.
4. Cerca **Bolletta** e clicca su **Scarica**.
5. Riavvia Home Assistant.

### Metodo 2: Installazione Manuale

1. Scarica la cartella `custom_components/bolletta`.
2. Copiala nella directory `custom_components/` della tua installazione di Home Assistant:
   ```text
   /config/custom_components/bolletta/
   ```
3. Riavvia Home Assistant.

---

## ⚙️ Configurazione

1. Nella WebUI di Home Assistant, vai su **Impostazioni** -> **Dispositivi e Servizi**.
2. Clicca su **Aggiungi Integrazione** in basso a destra e cerca **Bolletta (Luce, Acqua, Gas)**.
3. Seleziona la **Tipologia di Fornitura**:
   - ⚡ **Energia Elettrica**
   - 💧 **Acqua / Servizio Idrico**
   - 🔥 **Gas Naturale**

### Configurazione Energia Elettrica:
1. **Passo Generale**: Assegna un nome all'istanza (es. *Bolletta Luce Casa*), scegli il fornitore tra quelli in `operators/energy/`, seleziona la potenza impegnata (es. `3.0 kW`, `4.5 kW`, `6.0 kW`) e abilita la tariffa multioraria.
2. **Passo Offerta Commerciale**: Seleziona l'offerta specifica del venditore (es. *Energia Chiara*, *Octopus Flex*, ecc.). I parametri e le formule vengono precaricati automaticamente dal file corrispondente.
3. **Passo Sensori PUN**: Seleziona i tuoi sensori PUN esistenti in Home Assistant (F0 se monorario, oppure F1, F2, F3 se multiorario).
4. **Passo Parametri Contrattuali**: Verifica o personalizza i parametri del venditore (Spread/CCL, PCV, Dispacciamento PD, Accisa, IVA, ecc.).
5. **Passo Collegamento ARERA**: Conferma o seleziona le entità ARERA rilevate automaticamente (incluso `sensor.arera_dispbt`).

### Configurazione Acqua / Servizio Idrico:
1. **Passo Generale**: Assegna un nome all'istanza (es. *Bolletta Acqua Acea*), scegli il gestore (es. *Acea Ato 2 / Ato 5* o *Personalizzato*) e seleziona l'entità sensore del contatore dell'acqua (lettura volumetrica in $\text{m}^3$).
2. **Passo Offerta / Tipologia Utenza**: Seleziona l'offerta (es. *Domestico Residente (TICSI)*).
3. **Passo Parametri Tariffari**: Verifica le quote fisse (€/anno per acquedotto, fognatura, depurazione), le soglie degli scaglioni annui ($\text{m}^3$), le relative tariffe al $\text{m}^3$, i costi fognatura/depurazione, gli oneri di perequazione ARERA ($UI_1, UI_2, UI_3$) e l'IVA (10%).

> [!TIP]
> Puoi modificare qualsiasi parametro contrattuale o tariffario in ogni momento cliccando su **Configura / Opzioni** sulla scheda dell'integrazione senza dover riavviare.

---

## 💧 Come Funziona il Calcolo della Bolletta Acqua (ARERA TICSI)

La tariffazione idrica in Italia segue il Testo Integrato Corrispettivi Servizi Idrici (**TICSI**, Delibera ARERA 665/2017/R/idr). Il calcolo implementato in Bolletta riflette fedelmente tale modello:

### 1. Quota Fissa
Somma delle quote fisse annuali divise per 365 per ottenere l'impatto giornaliero:
$$\text{QF}_{\text{tot}} = \text{QF}_{\text{idrico}} + \text{QF}_{\text{fognatura}} + \text{QF}_{\text{depurazione}}$$

### 2. Contabilizzazione Annuale Solare (1 Gennaio - 31 Dicembre)
Secondo le regole ARERA TICSI, gli scaglioni di consumo sono espressi in $\text{m}^3\text{/anno}$ e si riferiscono tassativamente all'**anno solare (dal 1° gennaio al 31 dicembre)**:
- L'integrazione espone l'entità nativa `sensor.<istanza>_consumo_annuo_acqua` ($\text{m}^3$, `total_increasing`) che traccia il consumo netto maturato dal 1° gennaio.
- **Se usi un contatore cumulativo a lettura assoluta** (es. contatore a impulsi che segna $380\text{ m}^3$ continuativi), puoi impostare la lettura al 1° gennaio (`water_annual_baseline`). Il calcolo utilizzerà:
  $$\text{Consumo Annuo} = \text{Lettura Attuale} - \text{Lettura al 1° Gennaio}$$
- **Reset automatico di Capodanno**: alla mezzanotte del 31 dicembre (passaggio al 1° gennaio alle 00:00:05), l'integrazione acquisisce automaticamente la nuova lettura come baseline del nuovo anno solare e azzera il conteggio annuo, facendo ripartire la fatturazione dallo scaglione di Tariffa Agevolata.
- **Se colleghi un sensore già annuale** (es. `utility_meter` con `cycle: yearly`), puoi lasciare la baseline a 0 e il sensore verrà utilizzato direttamente.

### 3. Quota Variabile Idrico (a Scaglioni Progressivi)
Il consumo annuo in $\text{m}^3$ viene ripartito progressivamente su 5 scaglioni:
- **Tariffa Agevolata**: per consumi da $0$ a $S_1$ (default $55\text{ m}^3$)
- **Tariffa Base**: per consumi da $S_1$ a $S_2$ (default $108\text{ m}^3$)
- **I Eccedenza**: per consumi da $S_2$ a $S_3$ (default $162\text{ m}^3$)
- **II Eccedenza**: per consumi da $S_3$ a $S_4$ (default $216\text{ m}^3$)
- **III Eccedenza**: per consumi superiori a $S_4$ ($> 216\text{ m}^3$)

### 4. Fognatura, Depurazione e Oneri Perequativi ARERA
- **Fognatura**: $\text{Consumo Annuo} \times T_{\text{fognatura}}$ (escludibile via switch)
- **Depurazione**: $\text{Consumo Annuo} \times T_{\text{depurazione}}$ (escludibile via switch)
- **Componenti Perequative ARERA**: $\text{Consumo Annuo} \times (UI_1 + UI_2 + UI_3)$
  - $UI_1$: Agevolazioni tariffarie per eventi sismici
  - $UI_2$: Promozione della qualità dei servizi idrici
  - $UI_3$: Fondo sociale idrico nazionale per utenze disagiate

### 5. Totale Bolletta
$$\text{Imponibile} = \text{QF}_{\text{tot}} + \text{Variabile Idrico} + \text{Fognatura} + \text{Depurazione} + \text{Oneri } UI$$
$$\text{Costo Totale Acqua} = \text{Imponibile} \times \left(1 + \frac{\text{IVA}}{100}\right)$$

---

## 🛠️ Come Creare Operatori e Offerte Personalizzate

Tutti gli operatori e le relative offerte risiedono nella cartella `custom_components/bolletta/operators/`, suddivisi per commodity:

```text
custom_components/bolletta/operators/
├── energy/                       <-- Fornitori Energia Elettrica
│   ├── engie/
│   │   ├── operator.json
│   │   ├── energia_chiara.json
│   │   └── ...
│   ├── octopus/
│   ├── dolomiti/
│   └── custom/
│       ├── operator.json
│       ├── personalizzata.json
│       └── personalizzata_xml.xml
├── water/                        <-- Gestori Servizio Idrico
│   ├── acea/
│   │   ├── operator.json
│   │   └── domestico_residente.json
│   └── custom/
│       ├── operator.json
│       └── personalizzata.json
└── gas/                          <-- Fornitori Gas Naturale
    └── custom/
        ├── operator.json
        └── personalizzata.json
```

### Struttura di un File Offerta Acqua (`.json`)
```json
{
  "id": "domestico_residente",
  "name": "Domestico Residente (TICSI)",
  "description": "Tariffa idrica domestica per residenti secondo Delibera ARERA TICSI",
  "qf_idrico": 18.25,
  "qf_fognatura": 5.48,
  "qf_depurazione": 10.95,
  "usa_fognatura_depurazione": true,
  "s1": 55.0,
  "s2": 108.0,
  "s3": 162.0,
  "s4": 216.0,
  "t_agevolata": 0.5218,
  "t_base": 1.1542,
  "t_ecc1": 1.8421,
  "t_ecc2": 2.4510,
  "t_ecc3": 3.1250,
  "t_fognatura": 0.2315,
  "t_depurazione": 0.4820,
  "ui1": 0.004,
  "ui2": 0.009,
  "ui3": 0.005,
  "iva": 10.0
}
```

---

## 📑 Entità Generate

### Entità per Energia Elettrica (Luce)
| Entità | Descrizione | Unità | Classe |
| :--- | :--- | :--- | :--- |
| `sensor.<istanza>_prezzo_unitario_attuale` | **Prezzo in tempo reale** della fascia oraria attiva | EUR/kWh | measurement |
| `sensor.<istanza>_fascia_attuale` | Fascia oraria ARERA attiva (**F1**, **F2**, **F3**) | - | - |
| `sensor.<istanza>_prezzo_unitario_f0` | Prezzo finito tariffa Monoraria (F0) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f1` | Prezzo finito fascia Picco (F1) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f2` | Prezzo finito fascia Intermedia (F2) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_unitario_f3` | Prezzo finito fascia Fuori Picco (F3) | EUR/kWh | measurement |
| `sensor.<istanza>_prezzo_fisso_giornaliero` | Quota fissa giornaliera (PCV + ARERA + Potenza) | EUR/day | measurement |
| `sensor.<istanza>_costo_fisso_mensile` | Quota fissa media mensile | EUR/month | measurement |
| `sensor.<istanza>_potenza_impegnata` | **Potenza impegnata** da contratto (con attributi soglie sgancio) | kW | power |

### Entità per Acqua / Servizio Idrico
| Entità | Tipo | Descrizione | Unità |
| :--- | :--- | :--- | :--- |
| `sensor.<istanza>_consumo_annuo_acqua` | Sensore | **Consumo d'acqua dell'anno solare in corso** (1 Gen - 31 Dic) | m³ |
| `sensor.<istanza>_costo_acqua_totale` | Sensore | **Costo totale calcolato** (IVA inclusa) sul consumo | EUR |
| `sensor.<istanza>_prezzo_medio_m3` | Sensore | Prezzo medio finito per $\text{m}^3$ consumato | EUR/m³ |
| `sensor.<istanza>_scaglione_acqua` | Sensore | Nome dello scaglione TICSI attualmente raggiunto | - |
| `sensor.<istanza>_quota_fissa_giornaliera_acqua` | Sensore | Quota fissa complessiva giornaliera | EUR/day |
| `sensor.<istanza>_quota_fissa_annua_acqua` | Sensore | Quota fissa complessiva annua | EUR/year |
| `sensor.<istanza>_quota_variabile_acqua` | Sensore | Quota variabile complessiva imponibile | EUR |
| `switch.<istanza>_fognatura` | Interruttore | **Abilita/disabilita fognatura** nel calcolo (fissa + variabile) | - |
| `switch.<istanza>_depurazione` | Interruttore | **Abilita/disabilita depurazione** nel calcolo (fissa + variabile) | - |

---

## 📊 Integrazione con la Dashboard Energia di Home Assistant

Per associare il prezzo dinamico dell'energia elettrica o il costo dell'acqua alla **Dashboard Energia**:
1. Vai su **Impostazioni** -> **Dashboard** -> **Energia**.
2. **Per l'Energia Elettrica**: in *Rete elettrica* seleziona `sensor.<istanza>_prezzo_unitario_attuale` come entità di prezzo.
3. **Per l'Acqua**: nella sezione *Consumo d'acqua*, seleziona il tuo sensore di consumo volumetrico ($\text{m}^3$) e imposta come tracciamento costi `sensor.<istanza>_prezzo_medio_m3` oppure `sensor.<istanza>_costo_acqua_totale`.

---

## 🛠️ Integrazione Compagna ARERA

Per recuperare automaticamente e mantenere aggiornate le tariffe regolate di rete, gli oneri di sistema e la componente **DispBT** direttamente dai portali ufficiali ARERA per l'energia elettrica, installa l'integrazione compagna:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 Licenza

Distribuito sotto licenza GNU General Public License v3.0 (GPLv3). Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
