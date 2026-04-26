import pandas as pd
from pathlib import Path

from Modules import module_work_shift


SECTOR_CODE_BY_INDUSTRY_NUMBER = {
    1: "ISI",
    2: "NFM",
    3: "CHI",
    4: "NMM",
    5: "PPA",
    6: "FBT",
    7: "TRE",
    8: "MAE",
    9: "TEL",
    10: "WWP",
    11: "OIS",
}

BASE_ELECTRIC_COLUMNS = [
    "Lighting",
    "Air compressors",
    "Motor drives",
    "Fans and pumps",
    "Low-enthalpy heat",
    "Others (sum mean)",
]

WEIGHT_MODE_FILES = {
    "summed": {
        "folder": "JRC-IDEES_final_energy_consumption_by_country_aggregated6_total",
        "filename_template": "{country_code}_final_energy_consumption_aggregated6_total.xlsx",
    },
    "unsummed": {
        "folder": "JRC-IDEES_final_energy_consumption_by_country_rerun",
        "filename_template": "{country_code}_final_energy_consumption.xlsx",
    },
}


def _resolve_root(base_path):
    """
    Resolve project root from an optional file/folder path.
    """
    root = Path(base_path) if base_path else Path(__file__).resolve().parent.parent
    if root.suffix:
        root = root.parent
    return root


def _build_year_map(df):
    """
    Build a {year: column_index} map from the first row of an IDEES sheet.
    """
    year_map = {}
    for c in range(1, df.shape[1]):
        value = df.iat[0, c]
        if pd.notna(value):
            year_map[int(value)] = c
    return year_map


def _select_year_column(year_map, year):
    """
    Select target year column, falling back to the latest available year.
    """
    selected_year = int(year) if int(year) in year_map else max(year_map.keys())
    return year_map[selected_year]


def _weights_file_path(root, country_code, mode):
    """
    Build absolute path to the weights workbook for the selected mode.
    """
    config = WEIGHT_MODE_FILES[mode]
    return (
        root
        / "Data"
        / "General"
        / config["folder"]
        / config["filename_template"].format(country_code=country_code)
    )


def _read_sector_weights_from_aggregated(workbook_path, sector_code, year):
    """
    Read sector weights from the aggregated workbook (summed mode).
    """
    df = pd.read_excel(workbook_path, sheet_name=sector_code, header=None)
    year_map = _build_year_map(df)
    year_col = _select_year_column(year_map, year)

    weights = {name: 0.0 for name in BASE_ELECTRIC_COLUMNS}
    for r in range(1, df.shape[0]):
        label = df.iat[r, 0]
        if not isinstance(label, str):
            continue
        clean_label = label.strip()
        if clean_label in weights:
            weights[clean_label] = float(df.iat[r, year_col])

    return pd.Series(weights, dtype=float)


def _sheet_matches_sector(sheet_name, sector_code):
    """
    Match workbook sheet names to a sector code prefix.
    """
    clean = str(sheet_name).strip().upper()
    sector = str(sector_code).strip().upper()
    return (
        clean == sector
        or clean.startswith(f"{sector} ")
        or clean.startswith(f"{sector}-")
        or clean.startswith(f"{sector}_")
    )


def _read_unsummed_rows(df, year_col):
    """
    Read all end-use rows from a sector sheet for one year (excluding Total/Others row).
    """
    rows = {}

    for r in range(1, df.shape[0]):
        label = df.iat[r, 0]
        if not isinstance(label, str):
            continue
        clean_label = label.strip()
        if not clean_label or clean_label.lower() == "total (%)" or clean_label == "Others (sum mean)":
            continue

        value = float(df.iat[r, year_col])
        rows[clean_label] = value

    return rows


def _read_sector_weights_from_sector_sheets(workbook_path, sector_code, year):
    """
    Read sector weights from rerun workbook and average across matching subsector sheets.
    """
    with pd.ExcelFile(workbook_path) as xls:
        sector_sheets = [name for name in xls.sheet_names if _sheet_matches_sector(name, sector_code)]
        sheet_rows = []
        for sheet_name in sector_sheets:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            year_map = _build_year_map(df)
            year_col = _select_year_column(year_map, year)
            sheet_rows.append(_read_unsummed_rows(df, year_col))

    n_sheets = len(sheet_rows)
    sum_weights = {}
    for rows in sheet_rows:
        for label, value in rows.items():
            sum_weights[label] = sum_weights.get(label, 0.0) + value

    mean_weights = {label: total / n_sheets for label, total in sum_weights.items()}

    return pd.Series(mean_weights, dtype=float)


def _read_sector_weights(root, country_code, industry_number, year, weights_mode="summed"):
    """
    Read electric application weights for one sector and one year.
    """
    sector_code = SECTOR_CODE_BY_INDUSTRY_NUMBER[int(industry_number)]
    weights_path = _weights_file_path(root, country_code, weights_mode)

    if weights_mode == "unsummed":
        return _read_sector_weights_from_sector_sheets(weights_path, sector_code, year)
    return _read_sector_weights_from_aggregated(weights_path, sector_code, year)


def _project_profiles_to_base_categories(profile_df):
    """
    Map legacy end-user profiles to the 6-category structure used by sector weights.
    """
    out = pd.DataFrame(index=profile_df.index)

    zeros = pd.Series(0.0, index=profile_df.index)

    out["Lighting"] = profile_df["Lighting"] if "Lighting" in profile_df.columns else zeros
    out["Air compressors"] = (
        profile_df["Discontinuous mechanical drive"]
        if "Discontinuous mechanical drive" in profile_df.columns
        else zeros
    )
    out["Motor drives"] = (
        profile_df["Continuous mechanical drive"]
        if "Continuous mechanical drive" in profile_df.columns
        else zeros
    )
    out["Fans and pumps"] = (
        profile_df["Process cooling"]
        if "Process cooling" in profile_df.columns
        else zeros
    )

    heat_cols = [c for c in ["Space heating", "Hot water", "Process heat"] if c in profile_df.columns]
    out["Low-enthalpy heat"] = profile_df[heat_cols].mean(axis=1) if heat_cols else zeros

    other_cols = [c for c in ["Space cooling", "ICT"] if c in profile_df.columns]
    out["Others (sum mean)"] = profile_df[other_cols].mean(axis=1) if other_cols else zeros

    return out


def _expand_unsummed_profiles(profile_df, usage_labels):
    """
    Expand base profiles so unsummed end-use labels map to concrete profile columns.
    """
    out = pd.DataFrame(index=profile_df.index)
    others_profile = profile_df["Others (sum mean)"]

    for label in usage_labels:
        if label in profile_df.columns and label != "Others (sum mean)":
            out[label] = profile_df[label]
        else:
            out[label] = others_profile

    return out


def _read_enduser_profiles(base_path, sheet_name):
    """
    Read an end-user profile sheet and drop empty rows.
    """
    root = _resolve_root(base_path)

    data_path = root / "Data" / "ElectricalSpecific" / "Load_profiles_enduser.xlsx"
    df = pd.read_excel(
        data_path,
        index_col=0,
        sheet_name=sheet_name,
    )
    df = df.dropna(axis=0)
    return df


def _read_base_electric_profiles(base_path):
    """
    Read and project all daily electric end-user profiles to base categories.
    """
    return {
        "weekday": _project_profiles_to_base_categories(_read_enduser_profiles(base_path, "Week_day")),
        "saturday": _project_profiles_to_base_categories(_read_enduser_profiles(base_path, "Saturday")),
        "sunday": _project_profiles_to_base_categories(_read_enduser_profiles(base_path, "Sunday")),
        "holiday": _project_profiles_to_base_categories(_read_enduser_profiles(base_path, "Holiday")),
    }


def _expand_profiles_for_mode(base_profiles, weights_mode, usage_labels):
    """
    Return day-type profiles adapted to selected weights mode.
    """
    if weights_mode == "unsummed":
        return {
            day_type: _expand_unsummed_profiles(df, usage_labels)
            for day_type, df in base_profiles.items()
        }
    return dict(base_profiles)


def _apply_profile_weights(profiles, weights):
    """
    Multiply profiles by column weights and add a total column.
    """
    y = profiles.mul(weights, axis=1)  # Application profiles * Share of applications
    y["Total"] = y.sum(axis=1)
    return y


def build_electric_daily_profiles(
    industry_number,
    year,
    country_code,
    base_path,
    apply_shifts=True,
    weights_mode="summed",
):
    """ INPUT: END USER PROFILES """
    base_profiles = _read_base_electric_profiles(base_path)

    """ INPUT: INDUSTRY DATA """
    root = _resolve_root(base_path)
    all_info_path = root / "Data" / "ElectricalSpecific" / "All_info_industry_types_electrical.xlsx"
    industry_info_df = pd.read_excel(all_info_path)
    industry_info_df.dropna(how="all", axis=0, inplace=True)
    industry_info_df.dropna(how="all", axis=1, inplace=True)
    industry_info_df.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = industry_info_df[industry_info_df.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    weights = _read_sector_weights(
        root=root,
        country_code=country_code,
        industry_number=industry_number,
        year=year,
        weights_mode=weights_mode,
    )

    expanded_profiles = _expand_profiles_for_mode(base_profiles, weights_mode, list(weights.index))
    profiles_weekday = expanded_profiles["weekday"]
    profiles_saturday = expanded_profiles["saturday"]
    profiles_sunday = expanded_profiles["sunday"]
    profiles_holiday = expanded_profiles["holiday"]

    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:, :] = 1

    if apply_shifts:
        shift_betas = {
            col: (
                0.85
                if col in {"Motor drives", "Air compressors", "Fans and pumps"}
                else 0.7
                if col == "Lighting"
                else 0.3
            )
            for col in profiles_weekday.columns
        }
        profiles_weekday, profiles_saturday, profiles_sunday, profiles_holiday = (
            module_work_shift.apply_work_shifts(
                profiles_weekday,
                profiles_saturday,
                profiles_sunday,
                profiles_holiday,
                shift_type=2,
                family="continuous",
                betas=shift_betas,
                ramp_minutes=(45, 45),
                rescale=True,
            )
        )

    weights = weights.reindex(profiles_weekday.columns).fillna(0.0)

    """ CREATE DAILY PROFILES """
    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type 
   
   
    
def build_thermal_daily_profiles(industry_number, base_path, apply_shifts=True):
    """ INPUT: END USER PROFILES """
    root = _resolve_root(base_path)
    thermal_data_path = root / "Data" / "HeatSpecific" / "Load_profiles_daytypes.xlsx"
    profiles_weekday = pd.read_excel(thermal_data_path, sheet_name="Week_day", index_col=0)
    profiles_saturday = pd.read_excel(thermal_data_path, sheet_name="Saturday", index_col=0) 
    profiles_sunday = pd.read_excel(thermal_data_path, sheet_name="Sunday", index_col=0)
    profiles_holiday = pd.read_excel(thermal_data_path, sheet_name="Holiday", index_col=0)
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] =1
    
    
    """ INPUT: INDUSTRY DATA """
    all_info_path = root / "Data" / "HeatSpecific" / "All_info_industry_types_thermal.xlsx"
    industry_info_df = pd.read_excel(all_info_path)
    industry_info_df.dropna(how="all",axis=0, inplace=True)
    industry_info_df.dropna(how="all",axis=1, inplace=True)
    industry_info_df.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = industry_info_df[industry_info_df.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    data_industry = data_industry_type.iloc[:, 3:9]  # Extracts temperature range values
    data_industry = data_industry.astype(float)


    """ CREATE DAILY PROFILES """   
    weights = data_industry.iloc[0]

    thermal_rename = {
        "Raumwärme": "Space heating",
        "Warmwasser": "Hot water",
        "Prozesswärme < 100 °C": "< 100 °C",
        "Prozesswärme 100 °C - 500 °C": "100 °C - 500 °C",
        "Prozesswärme 500 °C - 1000 °C": "500 °C - 1000 °C",
        "Prozesswärme > 1000 °C": ">1000 °C",
    }

    weekday_profiles = _apply_profile_weights(profiles_weekday, weights).rename(columns=thermal_rename)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights).rename(columns=thermal_rename)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights).rename(columns=thermal_rename)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights).rename(columns=thermal_rename)
    constant_profiles = _apply_profile_weights(profiles_constant, weights).rename(columns=thermal_rename)

    if apply_shifts:
        thermal_betas = {
            "< 100 °C": 0.3,
            "100 °C - 500 °C": 0.3,
            "500 °C - 1000 °C": 0.3,
            ">1000 °C": 0.3,
        }
        weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles = (
            module_work_shift.apply_work_shifts(
                weekday_profiles,
                saturday_profiles,
                sunday_profiles,
                holiday_profiles,
                shift_type=2,
                family="continuous",
                betas=thermal_betas,
                ramp_minutes=(45, 45),
                rescale=True,
            )
        )
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type
