# DEUSTO iDesign RES

Industrial annual profile generator for electrical and thermal demand.

The project combines IDEES sector shares, daily load shapes, calendar effects,
seasonality, and annual demand factors to generate:

- annual load profiles in `.xlsx`
- annual stacked diagrams in `.png`
- IDEES electrical weight workbooks in summed and unsummed formats

## Requirements

Python 3.10+ with:

```bash
pip install pandas numpy matplotlib holidays openpyxl
```

## Data Layout

Raw IDEES workbooks are expected under:

```text
Data/General/JRC-IDEES/<COUNTRY_CODE>/
```

Electrical weight workbooks are generated into two separate folders:

```text
Data/General/JRC-IDEES_final_energy_consumption_by_country_summed/
Data/General/JRC-IDEES_final_energy_consumption_by_country_unsummed/
```

The generated workbook names are:

```text
<COUNTRY_CODE>_final_energy_consumption_summed.xlsx
<COUNTRY_CODE>_final_energy_consumption_unsummed.xlsx
```

`summed` workbooks contain one sheet per sector with six aggregated electrical
categories:

- Lighting
- Air compressors
- Motor drives
- Fans and pumps
- Low-enthalpy heat
- Others (sum mean)

`unsummed` workbooks contain detailed end-use sheets per sector/subsector.

## Regenerating IDEES Weights

Regenerate summed six-category workbooks:

```bash
python Helpers/parse_unsummed.py
```

Regenerate unsummed detailed workbooks:

```bash
python Helpers/parse_summed.py
```

Both parsers ignore inactive IDEES subsector blocks when aggregating or reading
weights, so active sector totals are normalized to 1.

## Running Profiles

Use `main.py` as the entry point:

```bash
python main.py
```

Configuration is controlled by the constants at the top of `main.py`:

```python
GENERATE_ELECTRICAL_PROFILE = True
GENERATE_THERMAL_PROFILE = True
COUNTRY_CODE = "DE"
YEAR = 2018
ELECTRICAL_INDUSTRY_NUMBER = 1
ELECTRICAL_WEIGHTS_MODE = "summed"  # "summed" or "unsummed"
THERMAL_INDUSTRY_NUMBER = 1
```

Electrical sectors:

```text
1  ISI  Iron and steel
2  NFM  Non-ferrous metals
3  CHI  Chemicals
4  NMM  Non-metallic minerals
5  PPA  Pulp, paper and printing
6  FBT  Food, beverages and tobacco
7  TRE  Transport equipment
8  MAE  Machinery equipment
9  TEL  Textiles and leather
10 WWP  Wood and wood products
11 OIS  Other industrial sectors
```

## Outputs

Profile runs write to:

```text
Generated/load_profiles/
Generated/diagrams/
```

Electrical diagram names include the country, sector, year, and weight mode:

```text
iDesign_RES_ES_ISI_Iron_and_steel_2020_summed_Diagram.png
iDesign_RES_ES_ISI_Iron_and_steel_2020_unsummed_Diagram.png
```

Electrical diagram titles use the same format for both modes:

```text
WZ08 ISI Iron and steel | ES | 2020 | summed
WZ08 ISI Iron and steel | ES | 2020 | unsummed
```

## Pipeline

The calculation flow is split across four modules:

1. `module_1`: builds base daily profiles and applies summed or unsummed IDEES weights.
2. `module_2`: applies peak/base factors and redistribution by applications.
3. `module_3`: creates the yearly calendar, applies seasonality, and normalizes to 1000 MWh.
4. `module_4`: scales to real annual consumption and adds electrical fluctuations.

Main code locations:

- `main.py`: editable run configuration and profile orchestration.
- `Profiles/LoadGeneratorElectricity.py`: electrical profile pipeline.
- `Profiles/LoadGeneratorThermal.py`: thermal profile pipeline.
- `Helpers/parse_unsummed.py`: exports summed six-category IDEES weights.
- `Helpers/parse_summed.py`: exports unsummed detailed IDEES weights.
- `Modules/module_plot.py`: diagram rendering and naming.
