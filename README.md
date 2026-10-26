# Bolletta (Electricity, Water, Gas) - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/evlas/Bolletta?color=blue&style=flat-square)](https://github.com/evlas/Bolletta/releases)
[![Hassfest](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml/badge.svg)](https://github.com/evlas/Bolletta/actions/workflows/hacs.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.8%2B-blue.svg)](https://www.home-assistant.io/)

🌐 *English | [Versione in italiano](README.it.md)*

Professional **Home Assistant** integration to calculate transparently and in real-time the cost and fixed fees of domestic utility contracts in Italy (**Electricity**, **Water / Integrated Water Service**, and **Natural Gas**).

---

## 🚀 Key Features

- **Multi-Commodity Architecture (Electricity, Water, Gas)**:
  - During initial setup, choose your utility service type:
    - ⚡ **Electricity**: real-time calculation based on PUN (single-rate or multi-rate F1, F2, F3), supplier spread, network losses, fixed PCV charges, and automatic integration with regulated **ARERA** components.
    - 💧 **Water / Integrated Water Service**: progressive consumption tier model compliant with **ARERA TICSI** standards (Resolution 665/2017/R/idr), fixed fees (aqueduct, sewerage, wastewater treatment), sewage rates, and ARERA equalization surcharges ($UI_1$, $UI_2$, $UI_3$), featuring presets for operators like **Acea Ato 2 / Ato 5**.
    - 🔥 **Natural Gas**: ready-to-use architecture with customizable operator and offer (annual fixed fee, variable charge per $\text{Sm}^3$, excise duty, and regional surcharges).
- **Modular Operators & Offers Architecture (JSON & XML)**:
  - Each commodity has its own dedicated directory: `operators/energy/`, `operators/water/`, `operators/gas/`.
  - Each supplier has its own subdirectory, and each commercial plan is an independent `.json` or `.xml` file.
  - Adding new suppliers and plans requires zero Python code changes!
  - **Included Presets**:
    - **Electricity**: **Engie** (*Energia Chiara*, *Energia Relax*, *Rinnovo Variabile*), **Octopus Energy** (*Octopus Flex*, *Octopus Fissa 12M*), **Dolomiti Energia** (*Mitica Web / Flex*), **Custom** (JSON & XML).
    - **Water**: **Acea Ato 2 / Ato 5** (*Domestico Residente* compliant with TICSI), **Custom** (*Custom Water Tariff*).
    - **Gas**: **Custom** (*Custom Gas Tariff*).
- **Dynamic Mathematical Formula Engine (Electricity)**:
  - Each offer defines custom formulas for energy price (`formula_energia`) and annual fixed cost (`formula_quota_fissa`).
  - Supports indexed contracts, fixed-price contracts per kWh, custom discounts, or tiered formulas.
- **DispBT Decoupled (Sourced from ARERA)**:
  - `DispBT` is an official ARERA-regulated component retrieved dynamically from `sensor.arera_dispbt`.
- **Dynamic Italian Time-of-Use Bands (F1, F2, F3)**:
  - Automatically detects the current tariff band in real-time based on ARERA rules, weekday, hours, and Italian holidays.
- **100% WebUI Configuration (Config Flow & Options Flow)**: Guided setup and live updates directly from *Settings -> Devices & Services*.
- **Multi-Instance Support**: Add multiple utility contracts simultaneously (e.g. Home Electricity, Home Water, Vacation House Electricity).

---

## 📦 Installation

### Method 1: Via HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** -> Click the three dots menu in the top right corner -> **Custom repositories**.
3. Paste `https://github.com/evlas/Bolletta.git`, select the category **Integration**, and click **Add**.
4. Search for **Bolletta** and click **Download**.
5. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the `custom_components/bolletta` directory.
2. Copy it into your Home Assistant installation:
   ```text
   /config/custom_components/bolletta/
   ```
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In the Home Assistant WebUI, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** in the bottom right corner and search for **Bolletta (Luce, Acqua, Gas)**.
3. Select your **Utility Type**:
   - ⚡ **Electricity**
   - 💧 **Water**
   - 🔥 **Natural Gas**

### Electricity Configuration:
1. **General Step**: Name your instance (e.g., *Bolletta Luce Casa*), select your provider from `operators/energy/`, choose contracted power (e.g., `3.0 kW`, `4.5 kW`, `6.0 kW`), and enable time-of-use tariffs.
2. **Commercial Offer Step**: Choose the specific tariff plan (e.g., *Energia Chiara*, *Octopus Flex*, etc.). Parameters and formulas are loaded automatically.
3. **PUN Sensors Step**: Select your existing Home Assistant sensors for PUN (F0 for single-rate, or F1, F2, F3 for multi-rate).
4. **Contract Parameters Step**: Review prefilled parameters (Spread/CCL, PCV, Dispatching, Excise, VAT 10%, etc.).
5. **ARERA Linking Step**: Select or confirm detected ARERA sensors (including `sensor.arera_dispbt`).

### Water Configuration:
1. **General Step**: Name your instance (e.g., *Bolletta Acqua Acea*), select the water provider (e.g., *Acea Ato 2 / Ato 5* or *Custom*), and pick the water meter volume sensor (reading in $\text{m}^3$).
2. **Offer Step**: Select the tariff plan (e.g., *Domestico Residente (TICSI)*).
3. **Tariff Parameters Step**: Review fixed annual fees (aqueduct, sewerage, depuration), tier thresholds ($\text{m}^3$), volumetric tier rates, sewerage/depuration unit rates, ARERA equalization surcharges ($UI_1, UI_2, UI_3$), and VAT (10%).

> [!TIP]
> You can modify any parameter anytime by clicking **Configure / Options** on the integration card without restarting.

---

## 💧 How Water Billing Works (ARERA TICSI)

Italian water billing follows the Integrated Water Services Tariff Framework (**TICSI**, ARERA Resolution 665/2017/R/idr):

### 1. Fixed Fee
Sum of annual fixed fees divided by 365 for a daily cost:
$$\text{QF}_{\text{tot}} = \text{QF}_{\text{aqueduct}} + \text{QF}_{\text{sewerage}} + \text{QF}_{\text{depuration}}$$

### 2. Calendar Year Accounting (Jan 1 - Dec 31)
Under Italian ARERA TICSI standards, water consumption bands are structured on an **annual solar calendar cycle** (1 January – 31 December).
- The integration exposes a native entity `sensor.<instance>_consumo_annuo_acqua` ($\text{m}^3$, `total_increasing`) tracking net water consumed since 1 January.
- **If you use a cumulative / lifetime water meter** (e.g. an impulse pulse meter showing continuous $380\text{ m}^3$), you can set the meter reading as of 1 January (`water_annual_baseline`). The calculation will compute:
  $$\text{Annual Consumption} = \text{Current Meter Reading} - \text{Jan 1 Baseline}$$
- **Automatic New Year's Midnight Reset**: at midnight on 31 December (transitioning to 1 January at 00:00:05), the integration automatically captures the current meter reading as the new year's baseline and resets annual consumption to 0, restarting billing from the Subsidized Tier.
- **If you connect a sensor that already resets annually** (e.g. an HA `utility_meter` with `cycle: yearly`), leave the baseline at 0 and the sensor value will be used directly.

### 3. Variable Aqueduct Charge (Progressive Tiers)
Annual consumption in $\text{m}^3$ is progressively broken down across 5 tiers:
- **Subsidized Tier (Agevolata)**: $0 \le \text{volume} \le S_1$ (default $55\text{ m}^3$)
- **Base Tier**: $S_1 < \text{volume} \le S_2$ (default $108\text{ m}^3$)
- **Tier 1 Excess (I Eccedenza)**: $S_2 < \text{volume} \le S_3$ (default $162\text{ m}^3$)
- **Tier 2 Excess (II Eccedenza)**: $S_3 < \text{volume} \le S_4$ (default $216\text{ m}^3$)
- **Tier 3 Excess (III Eccedenza)**: $\text{volume} > S_4$ ($> 216\text{ m}^3$)

### 4. Sewerage, Wastewater Treatment & ARERA Equalization
- **Sewerage**: $\text{Annual Volume} \times T_{\text{sewerage}}$ (can be disabled via options or switch)
- **Depuration**: $\text{Annual Volume} \times T_{\text{depuration}}$ (can be disabled via options or switch)
- **ARERA Equalization Surcharges**: $\text{Annual Volume} \times (UI_1 + UI_2 + UI_3)$
  - $UI_1$: Tariff relief for earthquake recovery
  - $UI_2$: Water service quality promotion
  - $UI_3$: National water social bonus

### 5. Total Water Bill
$$\text{Taxable Base} = \text{QF}_{\text{tot}} + \text{Variable Aqueduct} + \text{Sewerage} + \text{Depuration} + UI\text{ Charges}$$
$$\text{Total Water Cost} = \text{Taxable Base} \times \left(1 + \frac{\text{VAT}}{100}\right)$$

---

## 🛠️ Creating Custom Operators & Offers

All operators and offers reside under `custom_components/bolletta/operators/` by commodity:

```text
custom_components/bolletta/operators/
├── energy/                       <-- Electricity Providers
│   ├── engie/
│   │   ├── operator.json
│   │   ├── energia_chiara.json
│   │   └── ...
│   ├── octopus/
│   ├── dolomiti/
│   └── custom/
├── water/                        <-- Water Utilities
│   ├── acea/
│   │   ├── operator.json
│   │   └── domestico_residente.json
│   └── custom/
│       ├── operator.json
│       └── personalizzata.json
└── gas/                          <-- Natural Gas Providers
    └── custom/
        ├── operator.json
        └── personalizzata.json
```

---

## 📑 Generated Entities

### Electricity Entities
| Entity | Description | Unit | Class |
| :--- | :--- | :--- | :--- |
| `sensor.<instance>_prezzo_unitario_attuale` | **Real-time price** of currently active time-of-use band | EUR/kWh | measurement |
| `sensor.<instance>_fascia_attuale` | Active ARERA time-of-use band (**F1**, **F2**, **F3**) | - | - |
| `sensor.<instance>_prezzo_unitario_f0` | Total finished single-rate price (F0) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f1` | Total finished peak band price (F1) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f2` | Total finished intermediate band price (F2) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_unitario_f3` | Total finished off-peak band price (F3) | EUR/kWh | measurement |
| `sensor.<instance>_prezzo_fisso_giornaliero` | Daily fixed charges (PCV + ARERA + Capacity) | EUR/day | measurement |
| `sensor.<instance>_costo_fisso_mensile` | Monthly average fixed charges | EUR/month | measurement |
| `sensor.<instance>_potenza_impegnata` | Contracted power (with load disconnection threshold attributes) | kW | power |

### Water Entities
| Entity | Type | Description | Unit |
| :--- | :--- | :--- | :--- |
| `sensor.<instance>_consumo_annuo_acqua` | Sensor | **Annual water consumed** (1 Jan - 31 Dec) | m³ |
| `sensor.<instance>_costo_acqua_totale` | Sensor | **Total calculated bill cost** (incl. VAT) for consumption | EUR |
| `sensor.<instance>_prezzo_medio_m3` | Sensor | Average finished price per $\text{m}^3$ consumed | EUR/m³ |
| `sensor.<instance>_scaglione_acqua` | Sensor | Current active TICSI consumption tier reached | - |
| `sensor.<instance>_quota_fissa_giornaliera_acqua` | Sensor | Total daily fixed charges | EUR/day |
| `sensor.<instance>_quota_fissa_annua_acqua` | Sensor | Total annual fixed charges | EUR/year |
| `sensor.<instance>_quota_variabile_acqua` | Sensor | Total variable taxable charges | EUR |
| `switch.<instance>_fognatura` | Switch | **Enable/disable sewer** in calculation (fixed + variable) | - |
| `switch.<instance>_depurazione` | Switch | **Enable/disable purification** in calculation (fixed + variable) | - |

---

## 📊 Energy Dashboard Integration

To link finished electricity rates or water costs to Home Assistant's built-in **Energy Dashboard**:
1. Go to **Settings** -> **Dashboards** -> **Energy**.
2. **For Electricity**: under *Electricity grid*, set `sensor.<instance>_prezzo_unitario_attuale` as the price entity.
3. **For Water**: under *Water consumption*, select your volume sensor ($\text{m}^3$) and use `sensor.<instance>_prezzo_medio_m3` or `sensor.<instance>_costo_acqua_totale` for cost tracking.

---

## 🛠️ Companion ARERA Integration

To automatically sync and update regulated electricity network tariffs, system charges, and **DispBT** from official ARERA sources, install the companion integration:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 License

Distributed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE) for details.
