import sys
from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Modules import module_1, module_2, module_3, module_4, module_plot


"""
========================
    MANUAL SETTINGS:
========================

industry_number     industry_name
1                   ISI (Iron and steel)
2                   NFM (Non-ferrous metals)
3                   CHI (Chemicals)
4                   NMM (Non-metallic minerals)
5                   PPA (Pulp, paper and printing)
6                   FBT (Food, beverages and tobacco)
7                   TRE (Transport equipment)
8                   MAE (Machinery equipment)
9                   TEL (Textiles and leather)
10                  WWP (Wood and wood products)
11                  OIS (Other industrial sectors)

---

country_code        country_name
AT                  Austria
BE                  Belgium
BG                  Bulgaria
CY                  Cyprus
CZ                  Czech Republic
DE                  Germany
DK                  Denmark
EE                  Estonia
EL                  Greece
ES                  Spain
FI                  Finland
FR                  France
HR                  Croatia
HU                  Hungary
IE                  Ireland
IT                  Italy
LT                  Lithuania
LU                  Luxembourg
LV                  Latvia
MT                  Malta
NL                  Netherlands
PL                  Poland
PT                  Portugal
RO                  Romania
SE                  Sweden
SI                  Slovenia
SK                  Slovakia
"""

INDUSTRY_NUMBER = 1        # Select from list above
COUNTRY_CODE = "ES"        # Select a member from the EU
YEAR = 2020                # 2013-2023
WEIGHTS_MODE = "unsummed"  # "summed" or "unsummed"
BASE_PATH = ""


SECTOR_NAME_BY_CODE = {
    "ISI": "Iron and steel",
    "NFM": "Non-ferrous metals",
    "CHI": "Chemicals",
    "NMM": "Non-metallic minerals",
    "PPA": "Pulp, paper and printing",
    "FBT": "Food, beverages and tobacco",
    "TRE": "Transport equipment",
    "MAE": "Machinery equipment",
    "TEL": "Textiles and leather",
    "WWP": "Wood and wood products",
    "OIS": "Other industrial sectors",
}


def _build_year_profile(industry_number, year, country_code, base_path_str, weights_mode="summed"):
    # ========================
    #     RUN MODULE 1:
    # ========================
    weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type = (
        module_1.build_electric_daily_profiles(
            industry_number,
            year,
            country_code,
            base_path_str,
            weights_mode=weights_mode,
        )
    )

    # ========================
    #     RUN MODULE 2:
    # ========================
    weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted = module_2.apply_peak_base_factors(
        year,
        industry_number,
        data_industry_type,
        weekday_profiles,
        saturday_profiles,
        sunday_profiles,
        holiday_profiles,
        constant_profiles,
    )

    # ========================
    #     RUN MODULE 3:
    # ========================
    year_list, array_load_type = module_3.build_load_type_calendar(year)
    df = module_3.seasonality(
        year,
        year_list,
        array_load_type,
        weekday_adjusted,
        saturday_adjusted,
        sunday_adjusted,
        holiday_adjusted,
        constant_adjusted,
        base_path_str,
    )
    df_normalized = module_3.normalising_1000(df)

    # ========================
    #     RUN MODULE 4:
    # ========================
    df_scaled = module_4.upscale_yearly(year, industry_number, df_normalized, data_industry_type)
    df_with_fluctuations = module_4.add_fluctuations(industry_number, df_scaled, data_industry_type)

    return df_with_fluctuations, data_industry_type


def run(industry_number, year, base_path_str, weights_mode=WEIGHTS_MODE):
    base_path = Path(base_path_str) if base_path_str else PROJECT_ROOT
    base_path_str = str(base_path)

    df_with_fluctuations, data_industry_type = _build_year_profile(
        industry_number, year, COUNTRY_CODE, base_path_str, weights_mode=weights_mode
    )

    industry_type = module_1.SECTOR_CODE_BY_INDUSTRY_NUMBER.get(int(industry_number), str(industry_number))
    industry_name = SECTOR_NAME_BY_CODE.get(industry_type, industry_type)
    print(industry_name)

    # Save load data and diagrams
    diagrams_dir = base_path / "Generated" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    if weights_mode == "unsummed":
        module_plot.year_electrical_unsummed(
            df_with_fluctuations,
            industry_name,
            industry_type,
            COUNTRY_CODE,
            year,
            base_path,
        )
    else:
        module_plot.year_electrical_summed(df_with_fluctuations, industry_name, industry_type, base_path)

    # Create the LoadData folder if it doesn't exist
    load_data_dir = base_path / "Generated" / "load_profiles"
    load_data_dir.mkdir(parents=True, exist_ok=True)

    application_columns = [c for c in df_with_fluctuations.columns if c != "Total"]
    ordered_columns = application_columns + ["Total"]
    columns = pd.MultiIndex.from_arrays(
        [ordered_columns, ["in kW"] * len(ordered_columns)],
        names=("Application", "Unit"),
    )

    df_out = df_with_fluctuations[ordered_columns].copy()
    df_out.columns = columns
    df_out.index.name = "Time"
    df_out.to_excel(load_data_dir / f"iDesign_RES_{industry_name}_{industry_type}-{COUNTRY_CODE}.xlsx", index=True)

    return df_out


if __name__ == "__main__":
    run(INDUSTRY_NUMBER, YEAR, BASE_PATH, WEIGHTS_MODE)
