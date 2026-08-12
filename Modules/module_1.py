import pandas as pd
from pathlib import Path

from Modules import module_work_shift


BASE_ELECTRIC_COLUMNS = [
    "Lighting",
    "Air compressors",
    "Motor drives",
    "Fans and pumps",
    "Low-enthalpy heat",
    "Others (sum mean)",
]

HIGH_SHIFT_BETA_COLUMNS = {"Motor drives", "Air compressors", "Fans and pumps"}
MEDIUM_SHIFT_BETA_COLUMNS = {"Lighting", "Others (sum mean)"}

WEIGHT_MODE_FILES = {
    "summed": {
        "folder": "JRC-IDEES_final_energy_consumption_by_country_summed",
        "filename_template": "{country_code}_final_energy_consumption_summed.xlsx",
    },
    "sfu": {
        "folder": "JRC-IDEES_final_energy_consumption_by_country_summed",
        "filename_template": "{country_code}_final_energy_consumption_summed.xlsx",
    },
    "unsummed": {
        "folder": "JRC-IDEES_final_energy_consumption_by_country_unsummed",
        "filename_template": "{country_code}_final_energy_consumption_unsummed.xlsx",
    },
}

ELECTRIC_METADATA_INDUSTRY_BY_SECTOR = {
    "ISI": 9,   # Metal production
    "NFM": 10,  # Non-ferrous metals and foundries
    "CHI": 4,   # Basic chemicals
    "NMM": 8,   # Processing of stone and earth
    "PPA": 3,   # Paper manufacturing
    "FBT": 2,   # Food and tobacco
    "TRE": 13,  # Vehicle manufacturing
    "MAE": 12,  # Machinery manufacturing
    "TEL": 14,  # Other economic sectors
    "WWP": 14,  # Other economic sectors
    "OIS": 14,  # Other economic sectors
}


def _select_year_column(df, year):
    """Return the target year column, falling back to the latest available year."""
    year_map = {}
    for c in range(1, df.shape[1]):
        value = df.iat[0, c]
        if pd.notna(value):
            year_map[int(value)] = c

    selected_year = int(year) if int(year) in year_map else max(year_map.keys())
    return year_map[selected_year]


def _project_profiles_to_base_categories(profile_df):
    """
    Map legacy end-user profiles to the 6-category structure used by sector weights.
    """
    out = pd.DataFrame(index=profile_df.index)

    zeros = pd.Series(0.0, index=profile_df.index)
    numeric_profile = profile_df.apply(pd.to_numeric, errors="coerce")

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

    out["Others (sum mean)"] = (
        numeric_profile.mean(axis=1).fillna(0.0)
        if not numeric_profile.empty
        else zeros
    )

    return out


def _apply_profile_weights(profiles, weights):
    """
    Multiply profiles by column weights and add a total column.
    """
    y = profiles.mul(weights, axis=1)  # Application profiles * Share of applications
    y["Total"] = y.sum(axis=1)
    return y


def _read_electric_industry_metadata(root, industry_number, sector_code=None):
    """
    Read the electrical industry metadata row used by downstream modules.
    """
    all_info_path = (
        root
        / "Data"
        / "ElectricalSpecific"
        / "All_info_industry_types_electrical.xlsx"
    )
    industry_info_df = pd.read_excel(all_info_path)
    industry_info_df.dropna(how="all", axis=0, inplace=True)
    industry_info_df.dropna(how="all", axis=1, inplace=True)

    # Fill missing values only on numeric columns to avoid pandas StringDtype errors.
    numeric_cols = industry_info_df.select_dtypes(include="number").columns
    industry_info_df.loc[:, numeric_cols] = industry_info_df.loc[:, numeric_cols].fillna(0)

    sector = str(sector_code).strip().upper() if sector_code is not None else None
    metadata_industry_number = ELECTRIC_METADATA_INDUSTRY_BY_SECTOR.get(
        sector,
        industry_number,
    )
    selected = industry_info_df[industry_info_df.industry_number.eq(metadata_industry_number)].copy()
    if selected.empty:
        raise ValueError(
            f"No electrical metadata found for sector {sector_code or industry_number} "
            f"(metadata industry number {metadata_industry_number})."
        )

    selected["metadata_industry_number"] = selected["industry_number"]
    selected["industry_number"] = int(industry_number)
    selected["sector_code"] = sector
    return selected


def _read_electric_weights(root, weights_mode, country_code, sector_code, year):
    """
    Read country/year application shares for summed or unsummed IDEES workbooks.
    """
    weights_config = WEIGHT_MODE_FILES[weights_mode]
    weights_path = (
        root
        / "Data"
        / "General"
        / weights_config["folder"]
        / weights_config["filename_template"].format(country_code=country_code)
    )

    if weights_mode != "unsummed":
        return _read_summed_electric_weights(weights_path, sector_code, year)

    return _read_unsummed_electric_weights(weights_path, sector_code, year)


def _read_summed_electric_weights(weights_path, sector_code, year):
    """
    Read the six already-aggregated electrical categories from a summed workbook.
    """
    df = pd.read_excel(weights_path, sheet_name=sector_code, header=None)
    year_col = _select_year_column(df, year)
    weights = {name: 0.0 for name in BASE_ELECTRIC_COLUMNS}

    for r in range(1, df.shape[0]):
        label = df.iat[r, 0]
        if not isinstance(label, str):
            continue

        clean_label = label.strip()
        if clean_label in weights:
            weights[clean_label] = float(df.iat[r, year_col])

    weights = pd.Series(weights, dtype=float)
    total = weights.sum()
    return weights / total * 100.0 if total > 0.0 else weights


def _read_unsummed_electric_weights(weights_path, sector_code, year):
    """
    Read detailed end-use weights and average them across matching sector sheets.
    """
    sheet_weights = []

    sector = str(sector_code).strip().upper()
    with pd.ExcelFile(weights_path) as xls:
        for sheet_name in xls.sheet_names:
            if not _sheet_matches_sector(sheet_name, sector):
                continue

            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            weights = _read_unsummed_sheet_weights(df, year)
            if weights.sum() > 0.0:
                sheet_weights.append(weights)

    if not sheet_weights:
        return pd.Series(dtype=float)

    # Average detailed weights across active sector sheets that matched the code.
    weights = pd.concat(sheet_weights, axis=1).fillna(0.0).mean(axis=1)
    total = weights.sum()
    return weights / total * 100.0 if total > 0.0 else weights


def _sheet_matches_sector(sheet_name, sector):
    """
    Return True when an Excel sheet belongs to the requested sector code.
    """
    clean_name = str(sheet_name).strip().upper()
    return (
        clean_name == sector
        or clean_name.startswith(f"{sector} ")
        or clean_name.startswith(f"{sector}-")
        or clean_name.startswith(f"{sector}_")
    )


def _read_unsummed_sheet_weights(df, year):
    """
    Read detailed end-use rows from one unsummed sector sheet.
    """
    year_col = _select_year_column(df, year)
    weights = {}

    for r in range(1, df.shape[0]):
        label = df.iat[r, 0]
        if not isinstance(label, str):
            continue

        clean_label = label.strip()
        if (
            not clean_label
            or clean_label.lower() == "total (%)"
            or clean_label == "Others (sum mean)"
        ):
            continue

        weights[clean_label] = float(df.iat[r, year_col])

    return pd.Series(weights, dtype=float)


def _expand_profiles_for_weights(base_profiles, weights):
    """
    Expand base daily profiles so every detailed weight has a matching column.
    """
    expanded_profiles = {}
    usage_labels = list(weights.index)

    for day_type, profile in base_profiles.items():
        others_profile = profile["Others (sum mean)"]
        expanded_profile = pd.DataFrame(index=profile.index)

        for label in usage_labels:
            if label in profile.columns and label != "Others (sum mean)":
                expanded_profile[label] = profile[label]
            else:
                # Unknown detailed uses inherit the generic "Others" shape.
                expanded_profile[label] = others_profile

        expanded_profiles[day_type] = expanded_profile

    return expanded_profiles


def _read_thermal_industry_final_energy(root, country_code, industry_column):
    """
    Read final-energy values for one thermal industry column.
    """
    final_energy_path = (
        root
        / "Data"
        / "HeatSpecific"
        / "industry_heat_eu"
        / "industry_final_energy_consumption"
        / f"industry_final_energy_consumption_{country_code}.csv"
    )
    if not final_energy_path.exists():
        raise FileNotFoundError(f"Thermal final energy CSV not found: {final_energy_path}")

    final_energy_df = pd.read_csv(final_energy_path)
    if "energy_demand_type" not in final_energy_df.columns:
        raise KeyError(f"Missing 'energy_demand_type' column in {final_energy_path}")
    if industry_column not in final_energy_df.columns:
        raise KeyError(f"Missing '{industry_column}' column in {final_energy_path}")

    final_energy_values = pd.to_numeric(
        final_energy_df[industry_column],
        errors="coerce",
    ).fillna(0.0)

    return pd.Series(
        final_energy_values.to_numpy(),
        index=final_energy_df["energy_demand_type"].astype(str),
        dtype=float,
    )


def build_electric_daily_profiles(
    industry_number,
    sector_code,
    year,
    country_code,
    base_path,
    apply_shifts=True,
    weights_mode="summed",
):
    """Build electric daily profiles for weekday, Saturday, Sunday, holiday and constant loads."""
    root = Path(base_path) if base_path else Path(__file__).resolve().parent.parent

    # Read and project end-user daily profiles to the base electrical categories.
    profile_path = root / "Data" / "ElectricalSpecific" / "Load_profiles_enduser.xlsx"
    base_profiles = {}
    for day_type, sheet_name in {
        "weekday": "Week_day",
        "saturday": "Saturday",
        "sunday": "Sunday",
        "holiday": "Holiday",
    }.items():
        raw_profile = pd.read_excel(
            profile_path,
            index_col=0,
            sheet_name=sheet_name,
        ).dropna(axis=0)
        base_profiles[day_type] = _project_profiles_to_base_categories(raw_profile)

    # Read sector metadata and country/year application weights.
    data_industry_type = _read_electric_industry_metadata(root, industry_number, sector_code)
    weights = _read_electric_weights(root, weights_mode, country_code, sector_code, year)

    # Unsummed weights can contain detailed labels not present in the base profiles.
    expanded_profiles = (
        _expand_profiles_for_weights(base_profiles, weights)
        if weights_mode == "unsummed"
        else base_profiles
    )

    profiles_weekday = expanded_profiles["weekday"]
    profiles_saturday = expanded_profiles["saturday"]
    profiles_sunday = expanded_profiles["sunday"]
    profiles_holiday = expanded_profiles["holiday"]

    # Constant profiles keep the same application weights for every time step.
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:, :] = 1

    if apply_shifts:
        # Work-shift betas define how strongly each end use follows the schedule.
        shift_betas = {}
        for column in profiles_weekday.columns:
            if column in HIGH_SHIFT_BETA_COLUMNS:
                shift_betas[column] = 0.85
            elif column in MEDIUM_SHIFT_BETA_COLUMNS:
                shift_betas[column] = 0.7
            else:
                shift_betas[column] = 0.3

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

    # Align weights with the final profile columns before multiplying.
    weights = weights.reindex(profiles_weekday.columns).fillna(0.0)

    # Apply weights and add Total columns for every day type.
    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)

    return (
        weekday_profiles,
        saturday_profiles,
        sunday_profiles,
        holiday_profiles,
        constant_profiles,
        data_industry_type,
    )


def build_thermal_daily_profiles(
    industry_number,
    industry_name,
    industry_column,
    year,
    country_code,
    base_path,
    apply_shifts=True,
):
    """Build thermal daily profiles from Heat EU final-energy CSV shares."""
    country_code = str(country_code).upper()
    root = Path(base_path) if base_path else Path(__file__).resolve().parent.parent
    thermal_data_path = root / "Data" / "HeatSpecific" / "Load_profiles_daytypes.xlsx"
    base_weekday = pd.read_excel(thermal_data_path, sheet_name="Week_day", index_col=0)
    base_saturday = pd.read_excel(thermal_data_path, sheet_name="Saturday", index_col=0)
    base_sunday = pd.read_excel(thermal_data_path, sheet_name="Sunday", index_col=0)
    base_holiday = pd.read_excel(thermal_data_path, sheet_name="Holiday", index_col=0)

    final_energy = _read_thermal_industry_final_energy(root, country_code, industry_column)
    total_final_energy = float(final_energy.sum())
    if total_final_energy <= 0:
        raise ValueError(
            f"No final energy found for {industry_name} in {country_code}."
        )

    weights = final_energy / total_final_energy * 100.0
    usage_labels = list(weights.index)

    daily_profiles = {}
    for day_type, base_profile in {
        "weekday": base_weekday,
        "saturday": base_saturday,
        "sunday": base_sunday,
        "holiday": base_holiday,
    }.items():
        base_load = base_profile.iloc[:, 0].astype(float)
        daily_profiles[day_type] = pd.DataFrame(
            {label: base_load for label in usage_labels},
            index=base_profile.index,
        )

    profiles_weekday = daily_profiles["weekday"]
    profiles_saturday = daily_profiles["saturday"]
    profiles_sunday = daily_profiles["sunday"]
    profiles_holiday = daily_profiles["holiday"]

    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:, :] = 1

    data_industry_type = pd.DataFrame(
        [
            {
                "industry_number": int(industry_number),
                "WZ_ID": industry_name,
                "Name": industry_name,
                "Peak_factor": 0.0,
                "Base_factor": 0.0,
                f"Energy consumption {int(year)}": total_final_energy,
                f"Energieverbrauch {int(year)}": total_final_energy,
                "Country_code": country_code,
            }
        ],
        index=[int(industry_number)],
    )

    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)

    if apply_shifts:
        thermal_betas = {label: 0.3 for label in usage_labels}
        thermal_betas.update({"Electricity Other": 0.4, "Electricity Thermal": 0.3})
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
