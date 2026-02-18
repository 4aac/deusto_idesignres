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
1                   Mining and quarrying of stones and earth
2                   Food and tobacco
3                   Paper manufacturing
4                   Basic chemicals
5                   Other chemical industry
6                   Rubber and plastic goods
7                   Glass and ceramics
8                   Processing of stone and earth
9                   Metal production
10                  Non-ferrous metals and foundries
11                  Metal processing
12                  Machinery manufacturing
13                  Vehicle manufacturing
14                  Other economic sectors
"""

INDUSTRY_NUMBER = 12  # Select from list above
YEAR = 2020           # 2018, 2019, 2020
BASE_PATH = ""


def run(industry_number, year, base_path_str):
    base_path = Path(base_path_str) if base_path_str else PROJECT_ROOT
    base_path_str = str(base_path)
    # ========================
    #     RUN MODULE 1:
    # ========================
    weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type = (
        module_1.build_thermal_daily_profiles(industry_number, base_path_str)
    )

    industry_type = data_industry_type["WZ_ID"][industry_number]
    industry_name = str(data_industry_type["Name"][industry_number])
    print(industry_name)

    # ========================
    #     RUN MODULE 2:
    # ========================
    weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted = (
        module_2.apply_peak_base_factors(
            year,
            industry_number,
            data_industry_type,
            weekday_profiles,
            saturday_profiles,
            sunday_profiles,
            holiday_profiles,
            constant_profiles,
        )
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

    # Save thermal load data and diagrams
    diagrams_dir = base_path / "Generated" / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    module_plot.year_thermal(df_scaled, industry_name, industry_type, base_path)  # Plots and saves diagram

    # Create the LoadData folder if it doesn't exist
    load_data_dir = base_path / "Generated" / "load_profiles"
    load_data_dir.mkdir(parents=True, exist_ok=True)

    columns = pd.MultiIndex.from_arrays(
        [
            [
                "Space heating",
                "Hot water",
                "< 100 °C",
                "100 °C - 500 °C",
                "500 °C - 1000 °C",
                ">1000 °C",
                "Total",
            ],
            ["in kW"] * 7,
        ],
        names=("Application", "Unit"),
    )

    df_out = df_scaled.copy()
    df_out.columns = columns
    df_out.index.name = "Time"
    df_out.to_excel(load_data_dir / f"{industry_name} WZ08 {industry_type}.xlsx", index=True)

    return df_out


if __name__ == "__main__":
    run(INDUSTRY_NUMBER, YEAR, BASE_PATH)
