# DEUSTO iDesign RES

Industrial annual profile generator for:
- electrical demand
- thermal demand

The repository combines daily profiles, seasonality, and sector factors to produce:
- `.xlsx` files with annual profiles by application
- `.png` diagrams in `Generated/diagrams`

## Requirements

Python 3.10+ and these libraries:

```bash
pip install pandas numpy matplotlib holidays openpyxl
```

## How It Works

The calculation flow is split into 4 modules:

1. `module_1`: builds base daily profiles by day type (weekday, Saturday, Sunday, holiday, and constant loads).
2. `module_2`: applies peak/base factors and redistribution by applications.
3. `module_3`: creates the yearly calendar, applies seasonality (HDD), and normalizes to 1000 MWh.
4. `module_4`: scales to real annual consumption and (for electrical) adds fluctuations.

Main entry points:
- `ElectricalProfile/LoadGeneratorElectricity.py`
- `ThermalProfile/LoadGeneratorThermal.py`
- `main.py` (recommended CLI entry point to run electrical, thermal, or both)

## Quick Start (Recommended CLI)

Run both profiles with default values:

```bash
python main.py --non-interactive
```

Electrical example:

```bash
python main.py --profile electric --country ES --year 2020 --electric-industry 1 --weights-mode unsummed --non-interactive
```

Thermal example:

```bash
python main.py --profile thermal --country ES --year 2020 --thermal-industry 1 --non-interactive
```

## Outputs

After running:
- `Generated/load_profiles/`: annual profiles in Excel
- `Generated/diagrams/`: annual profile plots

## Image Examples

### Electrical Profile (ES, ISI, 2020, unsummed)

![Electrical profile ES ISI 2020](Generated/diagrams/iDesign_RES_ES_ISI_Iron_and_steel_2020_unsummed_rerun_Diagram.png)

### Thermal Profile (Primary Steel, ES)

![Thermal profile Primary Steel ES](Generated/diagrams/iDesign_RES_Primary%20Steel_ES_Diagram.png)

## Main Structure

- `main.py`: CLI interface (interactive and non-interactive).
- `ElectricalProfile/LoadGeneratorElectricity.py`: complete electrical pipeline.
- `ThermalProfile/LoadGeneratorThermal.py`: complete thermal pipeline.
- `Modules/module_1.py` to `Modules/module_4.py`: generation logic.
- `Modules/module_plot.py`: diagram rendering and saving.
