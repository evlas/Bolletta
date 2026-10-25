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

- **Configurazione 100% da WebUI (Config Flow & Options Flow)**: Aggiunta guidata, gestione e modifica dei parametri contrattuali da *Impostazioni -> Dispositivi e Servizi*, senza modificare file YAML e senza riavviare Home Assistant.
- **Preset Operatori Integrati**:
  - **Engie**: (es. *Energia Chiara / Relax* con contributo al consumo CCL, PCV, DispBT, dispacciamento PD, perdite di rete 10%).
  - **Octopus Energy**: (es. *Octopus Flex* con spread alfa, commercializzazione 8€/mese, DispBT, perdite di rete 10%).
  - **Dolomiti Energia**: (es. *Mitica Luce / Flex* con spread, commercializzazione 9.50€/mese, perdite di rete 10%).
  - **Personalizzato**: per configurare rapidamente qualunque altro fornitore italiano (A2A, Nen, Sorgenia, Iren, Enel, Eni Plenitude, ecc.).
- **Supporto Multi-Istanza**: Puoi aggiungere più contratti contemporaneamente (es. prima casa, seconda casa, o confrontare due operatori in tempo reale).
- **Fasce Orarie Italiane Dinamiche (F1, F2, F3)**:
  - Rileva automaticamente e in tempo reale la fascia attiva in base alle regole ARERA, giorno della settimana, orario e festività nazionali italiane (inclusa la Pasquetta calcolata con algoritmo astronomico).
  - Espone l'entità `sensor.<istanza>_prezzo_unitario_attuale`, che riflette all'istante il prezzo della fascia in vigore.
- **Integrazione con la Dashboard Energia di Home Assistant**:
  - Sensori configurati con `device_class: monetary`, `state_class: measurement` e valuta `EUR/kWh`.
  - Pronti per essere inseriti direttamente come tariffa dinamica nella Dashboard Energia ufficiale.
- **Collegamento Diretto con i Sensori PUN**: Selettore grafico nativo per agganciare i sensori PUN già presenti in Home Assistant (es. generati da HACS `pun_sensor`).
- **Integrazione con ARERA**:
  - Rileva e si aggancia automaticamente alle entità regolate dell'integrazione compagna **ARERA Tariffe Luce** (`sensor.arera_*`).
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
4. Segui la procedura guidata:
   - **Passo 1: Generale**: Assegna un nome all'istanza (es. *Bolletta Engie*), scegli l'operatore (**Engie**, **Octopus Energy**, **Dolomiti Energia** o **Personalizzato**), seleziona la potenza impegnata (es. `3.0 kW`, `4.5 kW`, `6.0 kW`) e abilita la tariffa multioraria.
   - **Passo 2: Sensori PUN**: Seleziona i tuoi sensori PUN esistenti in Home Assistant (F0, F1, F2, F3).
   - **Passo 3: Parametri Contrattuali**: Verifica i valori precompilati dell'offerta (Spread/CCL, PCV, DispBT, Dispacciamento, Accisa, IVA 10%, perdite di rete 10%).
   - **Passo 4: Collegamento ARERA**: Conferma o seleziona le entità ARERA rilevate.

> [!TIP]
> Puoi modificare qualsiasi parametro contrattuale, potenza impegnata o spread in ogni momento cliccando su **Configura / Opzioni** sulla scheda dell'integrazione senza dover riavviare.

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

## ⚡ Formule Matematiche di Calcolo

### Prezzo Unitario dell'Energia (€/kWh):
$$\text{Prezzo} = \left(\text{PUN} + \text{PDR}_{10\%} + \text{CCL} + \text{PD} + \text{PD}_{\text{forf}} + s_3 + \text{UC}_3 + \text{UC}_{6\text{qe}} + \text{ASOS} + \text{ARIM} + \text{Accisa}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)$$

Legenda:
- $\text{PUN}$: Prezzo Unico Nazionale (dal sensore PUN per F0, F1, F2 o F3).
- $\text{PDR}_{10\%}$: Perdite di rete standard in bassa tensione stabilite da ARERA ($0.10 \times \text{PUN}$).
- $\text{CCL}$: Contributo al consumo / spread del venditore (€/kWh).
- $\text{PD}$: Dispacciamento variabile (€/kWh).
- $\text{PD}_{\text{forf}}$: Dispacciamento forfettario (€/kWh).
- $s_3$: Quota energia trasporto e gestione contatore ARERA ($\sigma_3$).
- $\text{UC}_3, \text{UC}_{6\text{qe}}$: Componenti di perequazione e qualità ARERA.
- $\text{ASOS}, \text{ARIM}$: Oneri generali di sistema (rinnovabili e rimanenti oneri).
- $\text{Accisa}$: Imposta erariale di consumo (€/kWh, default 0.0227 €/kWh).
- $\text{IVA}$: Aliquota IVA (default 10%).

### Quota Fissa Giornaliera (€/giorno):
$$\text{Quota Fissa} = \frac{\left(\text{PCV} + \text{DispBT} + s_1 + s_2 \cdot \text{kW} + \text{UC}_{6\text{qp}} \cdot \text{kW}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)}{365}$$

Legenda:
- $\text{PCV}$: Corrispettivo di commercializzazione fissa del fornitore (€/anno).
- $\text{DispBT}$: Componente di dispacciamento BT (€/anno, tipicamente negativo ~ -10.77 €/anno).
- $s_1$: Quota fissa trasporto ARERA ($\sigma_1$, €/anno).
- $s_2$: Quota potenza trasporto ARERA ($\sigma_2$, €/kW/anno).
- $\text{UC}_{6\text{qp}}$: Quota potenza qualità ARERA (€/kW/anno).
- $\text{kW}$: Potenza impegnata del contatore (es. 3.0 kW).

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

Per recuperare automaticamente e mantenere aggiornate le tariffe regolate di rete e gli oneri di sistema, installa l'integrazione compagna:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 Licenza

Distribuito sotto licenza GNU General Public License v3.0 (GPLv3). Consulta il file [LICENSE](LICENSE) per ulteriori dettagli.
