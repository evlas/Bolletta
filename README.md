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

- **Modular Operators & Offers Architecture (JSON & XML)**:
  - Each supplier has its own directory in `custom_components/bolletta/operators/<operator_id>/`.
  - Each commercial offer (indexed to PUN, fixed-rate, custom formulas) is a standalone `.json` or `.xml` file.
  - Adding new suppliers and plans requires zero Python code changes!
  - **Included Presets**: **Engie** (*Energia Chiara*, *Energia Relax*), **Octopus Energy** (*Octopus Flex*, *Octopus Fissa 12M*), **Dolomiti Energia** (*Mitica Web / Flex*), **Custom Operator** (ready-to-use JSON and XML examples).
- **Dynamic Mathematical Formula Engine**:
  - Each offer defines its own formulas for energy price (`formula_energia`) and annual fixed cost (`formula_quota_fissa`).
  - Supports indexed contracts, fixed-price contracts per kWh, custom discounts, or tiered formulas.
- **DispBT Decoupled (Sourced from ARERA)**:
  - `DispBT` is no longer a static vendor fee; it is an official ARERA-regulated component retrieved dynamically from `sensor.arera_dispbt`.
- **100% WebUI Configuration (Config Flow & Options Flow)**: Step-by-step setup and live updates directly from *Settings -> Devices & Services*.
- **Multi-Instance Support**: Add multiple contracts simultaneously (e.g., primary home, vacation house, or compare two suppliers side-by-side in real-time).
- **Dynamic Italian Time-of-Use Bands (F1, F2, F3)**:
  - Automatically detects the current tariff band in real-time based on ARERA rules, day of the week, hours, and Italian national holidays (including Easter Monday calculated with an astronomical algorithm).
  - Exposes the `sensor.<instance>_prezzo_unitario_attuale` entity, reflecting the active band's price at any minute.
- **Seamless Home Assistant Energy Dashboard Integration**:
  - Entities formatted with `device_class: monetary`, `state_class: measurement`, and `unit_of_measurement: EUR/kWh`.
  - Ready to be plugged directly into the Energy Dashboard as the dynamic tariff price sensor.
- **Direct Link with Existing PUN Sensors**: Native graphical entity selector to bind existing PUN sensors (e.g. from HACS `pun_sensor`).
- **Seamless ARERA Integration**:
  - Automatically detects and links to regulated network tariffs from the companion **ARERA Tariffe Luce** integration (`sensor.arera_*`), including `sensor.arera_dispbt`.
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
   - **Step 1: General**: Name your contract instance (e.g., *Bolletta Engie*), choose your supplier from the list loaded from `operators/`, select contracted power (e.g., `3.0 kW`, `4.5 kW`, `6.0 kW`), and enable time-of-use tariffs.
   - **Step 2: Commercial Offer**: Pick the specific commercial plan (e.g., *Energia Chiara*, *Octopus Flex*, *Fixed Price*, etc.) dynamically loaded from JSON/XML files.
   - **Step 3: PUN Sensors**: Select your existing Home Assistant sensors for PUN (F0 for single-rate, or F1, F2, F3 for multi-rate).
   - **Step 4: Contract Parameters**: Review prefilled parameters inherited from the chosen offer (Spread/CCL, PCV, Dispatching, Excise, VAT 10%, etc.).
   - **Step 5: ARERA Linking**: Select or confirm detected ARERA sensors (including `sensor.arera_dispbt`).

> [!TIP]
> You can modify any parameter, contracted power, spread, or formula anytime by clicking **Configure / Options** on the integration card without restarting.

---

## 🛠️ Creating Custom Operators & Offers

Bolletta features a modular and extensible architecture. To add a new energy provider or custom tariff plan, simply create a folder and add `.json` or `.xml` definition files.

### 1. Directory Structure

All operators live under:
```text
custom_components/bolletta/operators/
├── <operator_id>/
│   ├── operator.json           <-- Operator metadata (mandatory)
│   ├── offer_1.json            <-- Offer definition in JSON (recommended)
│   ├── offer_2.xml             <-- Offer definition in XML (supported)
│   └── ...
```

### 2. Operator Metadata File (`operator.json` or `operator.xml`)

Create `operator.json` inside the operator's folder:
```json
{
  "id": "my_operator",
  "name": "My Energy Supplier",
  "description": "Supplier description (e.g. Free Market Provider)"
}
```

Or using XML format (`operator.xml`):
```xml
<?xml version="1.0" encoding="utf-8"?>
<operator>
  <id>my_operator</id>
  <name>My Energy Supplier</name>
  <description>Supplier description</description>
</operator>
```

### 3. Commercial Offer Files

Each `.json` or `.xml` file inside the operator's directory (other than `operator.*`) defines a selectable offer in the Config Flow.

#### Standard Offer Parameters:
- `id`: Unique identifier of the offer (e.g. `my_offer_flex`).
- `name`: Display name shown in the UI dropdown (e.g. `My Flex Plan (PUN + Spread)`).
- `description`: Short description of the contract.
- `ccl`: Supplier retail spread / consumption contribution in €/kWh (e.g. `0.015`).
- `pcv`: Fixed annual retail marketing fee in €/year (e.g. `72.00`).
- `pd`: Variable wholesale dispatching component in €/kWh (e.g. `0.0018`).
- `pd_forfettario`: Additional flat dispatching fee in €/kWh (e.g. `0.0`).
- `include_losses`: `true` to apply 10% grid losses to PUN, `false` otherwise.
- `accisa`: Italian electricity excise tax in €/kWh (default `0.0227`).
- `iva`: VAT rate percentage (default `10.0`).
- `formula_energia`: Custom mathematical formula calculating the final energy price (€/kWh).
- `formula_quota_fissa`: Custom mathematical formula calculating the annual fixed fee (€/year before dividing by 365).

> [!NOTE]
> `dispbt` must **not** be included in offer files: it is an ARERA-regulated component retrieved automatically in real time from `sensor.arera_dispbt`.

---

### 4. Mathematical Formula Engine

Formulas can contain any standard math operations (`+`, `-`, `*`, `/`, `**`, parentheses, numeric constants, and conditional expressions `x if c else y`).

#### Variables available in `formula_energia`:
| Variable | Description |
| :--- | :--- |
| `pun` | National Single Price (€/kWh) for the current band |
| `ccl` | Supplier spread or consumption contribution (€/kWh) |
| `pd` | Variable dispatching fee (€/kWh) |
| `pd_forfettario` | Flat dispatching fee (€/kWh) |
| `include_losses` | Boolean flag (whether 10% grid losses are applied) |
| `accisa` | Excise tax (€/kWh) |
| `iva` | VAT percentage (e.g. 10.0) |
| `s3` | ARERA transport and metering energy rate $\sigma_3$ (€/kWh) |
| `uc3` | ARERA equalization rate $\text{UC}_3$ (€/kWh) |
| `uc6_qe` | ARERA service quality energy rate $\text{UC}_{6\text{qe}}$ (€/kWh) |
| `asos` | ARERA renewable energy charges $\text{ASOS}$ (€/kWh) |
| `arim` | ARERA other system charges $\text{ARIM}$ (€/kWh) |
| *custom* | Any extra parameter defined in your offer JSON/XML |

#### Variables available in `formula_quota_fissa`:
| Variable | Description |
| :--- | :--- |
| `pcv` | Supplier retail marketing fixed fee (€/year) |
| `dispbt` | ARERA regulated component from `sensor.arera_dispbt` (€/year) |
| `s1` | ARERA fixed transport fee $\sigma_1$ (€/year) |
| `s2` | ARERA power capacity transport fee $\sigma_2$ (€/kW/year) |
| `uc6_qp` | ARERA power capacity quality fee $\text{UC}_{6\text{qp}}$ (€/kW/year) |
| `power_kw` | Contracted meter capacity in kW (e.g. 3.0, 4.5, 6.0) |
| `iva` | VAT percentage (e.g. 10.0) |
| *custom* | Any extra parameter defined in your offer JSON/XML |

---

### 5. Full Examples

#### Example 1: Indexed to PUN (`indexed_offer.json`)
```json
{
  "id": "indexed_plan",
  "name": "Dynamic Energy (PUN + Spread)",
  "description": "Monthly indexed PUN tariff with consumption spread",
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

#### Example 2: 12-Month Fixed Price Plan (`fixed_offer.json`)
Non-indexed tariff with fixed price per kWh (`prezzo_fisso_kwh`):
```json
{
  "id": "fixed_price_12m",
  "name": "Locked Rate 12M (Fixed Price)",
  "description": "Fixed electricity commodity price locked for 12 months",
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

#### Example 3: XML Format Offer (`custom_offer.xml`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<offer>
  <id>xml_offer_demo</id>
  <name>Custom XML Plan</name>
  <description>Sample contract with custom formula loaded from XML</description>
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

## ⚡ Reference Mathematical Formulas

### Energy Price per kWh (€/kWh):
$$\text{Price} = \left(\text{PUN} \times (1 + \text{PDR}) + \text{CCL} + \text{PD} + \text{PD}_{\text{forf}} + s_3 + \text{UC}_3 + \text{UC}_{6\text{qe}} + \text{ASOS} + \text{ARIM} + \text{Accisa}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)$$

### Daily Fixed Cost (€/day):
$$\text{Fixed Cost} = \frac{\left(\text{PCV} + \text{DispBT} + s_1 + s_2 \cdot \text{kW} + \text{UC}_{6\text{qp}} \cdot \text{kW}\right) \times \left(1 + \frac{\text{IVA}}{100}\right)}{365}$$

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

For fully automated, quarterly updated regulated network tariffs, system charges and the **DispBT** component directly from official ARERA tables, install the companion integration:
- 🔗 **[ARERA Tariffe Luce](https://github.com/evlas/Arera)**

---

## 📄 License

Distributed under the GNU General Public License v3.0 (GPLv3). See [LICENSE](LICENSE) for details.
