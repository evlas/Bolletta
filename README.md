# Bolletta Elettrica - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Bolletta?color=blue&style=flat-square)](https://github.com/evlas/Bolletta/releases)
[![Hassfest](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.8%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *English | [Versione in italiano](README.it.md)*

Professional **Home Assistant** integration to calculate transparently and in real-time the cost of electricity supply and fixed meter charges for Italian domestic energy contracts.

Easily links with existing **PUN** (Single National Price) sensors and regulated **ARERA** tariff components, supporting both single-rate (F0) and multi-rate time-of-use (F1, F2, F3) contracts.

---

## 🚀 Key Features

- **100% WebUI Configuration (Config Flow & Options Flow)**: Add, customize and update your electricity supplier and contract fees directly from *Settings -> Devices & Services* without touching YAML or restarting Home Assistant.
- **Built-in Supplier Presets**:
  - **Engie**: (e.g. *Energia Chiara / Relax* with CCL consumption fee, retail commercialization PCV, DispBT, dispatching PD, 10% grid losses).
  - **Octopus Energy**: (e.g. *Octopus Flex* with alpha spread, 8€/month PCV, DispBT, 10% grid losses).
  - **Dolomiti Energia**: (e.g. *Mitica Luce / Flex* with spread, 9.50€/month PCV, 10% grid losses).
  - **Custom (Personalizzato)**: Easily configure any other Italian supplier (A2A, Nen, Sorgenia, Iren, Enel, Eni Plenitude, etc.).
- **Multi-Instance Support**: Add multiple contracts simultaneously (e.g., primary home, vacation house, or compare two suppliers side-by-side in real-time).
- **Dynamic Italian Time-of-Use Bands (F1, F2, F3)**:
  - Automatically detects the current tariff band in real-time based on ARERA rules, day of the week, hours, and Italian national holidays (including Easter Monday calculated with an astronomical algorithm).
  - Exposes the `sensor.<instance>_prezzo_unitario_attuale` entity, reflecting the active band's price at any minute.
- **Seamless Home Assistant Energy Dashboard Integration**:
  - Entities formatted with `device_class: monetary`, `state_class: measurement`, and `unit_of_measurement: EUR/kWh`.
  - Ready to be plugged directly into the Energy Dashboard as the dynamic tariff price sensor.
- **Direct Link with Existing PUN Sensors**: Native graphical entity selector to bind existing PUN sensors (e.g. from HACS `pun_sensor`).
- **Seamless ARERA Integration**:
  - Automatically detects and links to regulated network tariffs from the companion **ARERA Tariffe Luce** integration (`sensor.arera_*`).
  - Includes robust official ARERA fallback defaults if the companion integration is not present.
- **Complete Fixed Cost Calculation**:
  - Calculates fixed daily cost (`EUR/day`) and estimated monthly cost (`EUR/month`) combining PCV, DispBT, power capacity fee, transport fixed fee, and VAT.

---

## 📦 Installation

### Method 1: Via HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** -> Click the three dots menu in the top right corner -> **Custom repositories**.
3. Paste `https://github.com/evlas/Bolletta.git`, select the category **Integration**, and click **Add**.
4. Search for **Bolletta Elettrica** and click **Download**.
5. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the `custom_components/bolletta` directory.
2. Copy it into your Home Assistant installation:
   ```
   /config/custom_components/bolletta/
   ```
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In the Home Assistant WebUI, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Bolletta Elettrica**.
4. Follow the setup wizard:
   - **Step 1: General**: Name your contract instance (e.g., *Bolletta Engie*), choose your supplier (**Engie**, **Octopus Energy**, **Dolomiti Energia**, **Custom**, or any added in `operators/`), select contracted power (e.g., `3.0 kW`, `4.5 kW`, `6.0 kW`), and enable time-of-use tariffs.
   - **Step 2: Commercial Offer**: Pick the specific commercial plan (e.g., *Energia Chiara*, *Octopus Flex*, etc.) dynamically loaded from JSON/XML files.
   - **Step 3: PUN Sensors**: Select your existing Home Assistant sensors for PUN (F0 for single-rate, or F1, F2, F3 for multi-rate).
   - **Step 4: Contract Parameters**: Review prefilled parameters inherited from the chosen offer (Spread/CCL, PCV, DispBT, Dispatching, Excise, VAT 10%, 10% grid losses).
   - **Step 5: ARERA Linking**: Select or confirm detected ARERA sensors.

> [!TIP]
> You can modify any parameter, contracted power, or spread anytime by clicking **Configure / Options** on the integration card without restarting.

---

## 📊 Energy Dashboard Integration

To use the dynamic tariff in Home Assistant's official **Energy Dashboard**:

1. Go to **Settings** -> **Dashboards** -> **Energy**.
2. Under **Electricity grid** -> **Grid consumption**, edit your energy meter consumption entity.
3. Under *Electricity price*, choose **Use an entity tracking the total costs or price**:
   - Select `sensor.<your_instance>_prezzo_unitario_attuale`

---

## 🎛️ Lovelace Card Example

Example Lovelace dashboard cards to monitor current electricity rates and fixed costs:

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

## ⚡ Mathematical Formulas

### Energy Price per kWh (€/kWh):
$$\text{Price} = \left(\text{PUN} + \text{PDR}_{10\%} + \text{CCL} + \text{PD} + \text{PD}_{\text{forf}} + s_3 + \text{UC}_3 + \text{UC}_{6\text{qe}} + \text{ASOS} + \text{ARIM} + \text{Accisa}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)$$

Where:
- $\text{PUN}$: National Single Price (from PUN sensor for F0, F1, F2, or F3).
- $\text{PDR}_{10\%}$: Standard ARERA low voltage network losses ($0.10 \times \text{PUN}$).
- $\text{CCL}$: Supplier retail spread / consumption contribution (€/kWh).
- $\text{PD}$: Variable dispatching component (€/kWh).
- $\text{PD}_{\text{forf}}$: Flat dispatching fee (€/kWh).
- $s_3$: ARERA transmission, distribution, and metering energy quota ($\sigma_3$).
- $\text{UC}_3, \text{UC}_{6\text{qe}}$: ARERA equalization and quality energy quotas.
- $\text{ASOS}, \text{ARIM}$: General system charges (renewables and remaining general charges).
- $\text{Accisa}$: Italian excise tax (€/kWh, default 0.0227 €/kWh).
- $\text{IVA}$: VAT percentage (default 10%).

### Daily Fixed Cost (€/day):
$$\text{Fixed Cost} = \frac{\left(\text{PCV} + \text{DispBT} + s_1 + s_2 \cdot \text{kW} + \text{UC}_{6\text{qp}} \cdot \text{kW}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)}{365}$$

Where:
- $\text{PCV}$: Supplier retail marketing fixed fee (€/year).
- $\text{DispBT}$: Low voltage dispatching component (€/year, typically negative ~ -10.77 €/year).
- $s_1$: ARERA fixed transport charge ($\sigma_1$, €/year).
- $s_2$: ARERA power capacity transport charge ($\sigma_2$, €/kW/year).
- $\text{UC}_{6\text{qp}}$: ARERA power capacity quality charge (€/kW/year).
- $\text{kW}$: Contracted meter capacity (e.g. 3.0 kW).

---

## 📑 Entities Created

| Entity | Description | Unit | Class |
| :--- | :--- | :--- | :--- |
| `sensor.<instance>_prezzo_unitario_attuale` | **Real-time price** for the currently active tariff band | EUR/kWh | measurement |
| `sensor.<instance>_fascia_attuale` | Currently active ARERA band (**F1**, **F2**, **F3**) | - | - |
| `sensor.<instance>_prezzo_unitario_f0` | Finished price for single-rate contract (F0) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f1` | Finished price for Peak band (F1) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f2` | Finished price for Mid-peak band (F2) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f3` | Finished price for Off-peak band (F3) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_fisso_giornaliero` | Daily fixed cost (PCV + ARERA + Capacity) | EUR/day | measurement |
| `sensor.<instance>_costo_fisso_mensile` | Estimated average monthly fixed cost | EUR/month | measurement |

---

## 🛠️ Companion ARERA Integration

For fully automated, quarterly updated regulated network and system charges, install the companion integration:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 License

Distributed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE) for details.
