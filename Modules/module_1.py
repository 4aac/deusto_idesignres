import pandas as pd
from pathlib import Path

from Modules import module_work_shift


def _resolve_project_root(base_path):
    if base_path:
        path = Path(base_path)
    else:
        path = Path(__file__).resolve().parent.parent

    if path.suffix:
        path = path.parent

    name = path.name.lower()
    parent_name = path.parent.name.lower() if path.parent else ""

    if name in {"electricalprofile", "thermalprofile"}:
        return path.parent
    if name == "data":
        if parent_name in {"electricalprofile", "thermalprofile"}:
            return path.parent.parent
        return path.parent
    if parent_name == "data" and name in {"electricalspecific", "heatspecific", "general"}:
        return path.parent.parent

    return path


def _resolve_existing_path(candidates):
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "None of the expected data files exist: " + ", ".join(str(c) for c in candidates)
    )


def _read_enduser_profiles(base_path, sheet_name):
    """
    Read an end-user profile sheet and drop empty rows.
    """
    project_root = _resolve_project_root(base_path)
    data_path = _resolve_existing_path(
        [
            project_root / "Data" / "ElectricalSpecific" / "Load_profiles_enduser.xlsx",
            project_root / "ElectricalProfile" / "data" / "Load_profiles_enduser.xlsx",
            project_root / "Electrical" / "Load_profiles_enduser.xlsx",
        ]
    )
    df = pd.read_excel(
        data_path,
        index_col=0,
        sheet_name=sheet_name,
    )
    df = df.dropna(axis=0)
    return df


def _apply_profile_weights(profiles, weights):
    """
    Multiply profiles by column weights and add a total column.
    """
    profile_columns = set(profiles.columns)
    weight_columns = set(weights.index)

    if profile_columns & weight_columns:
        y = profiles.mul(weights, axis=1)  # Application profiles * Share of applications
    elif profiles.shape[1] == 1:
        base = profiles.iloc[:, 0]
        y = pd.DataFrame({col: base * weights[col] for col in weights.index}, index=profiles.index)
    else:
        raise KeyError("Profile columns do not match weight columns, and no single base column found.")
    y["Total"] = y.sum(axis=1)
    return y


def _normalize_electric_profile_columns(df):
    df = df.copy()

    if "Mechanical drive" in df.columns and "Mechanical drives" not in df.columns:
        df = df.rename(columns={"Mechanical drive": "Mechanical drives"})
    return df


def build_electric_daily_profiles(industry_number, base_path, apply_shifts=True):
    """ INPUT: END USER PROFILES """
    profiles_weekday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Week_day"))
    profiles_saturday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Saturday"))
    profiles_sunday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Sunday"))
    profiles_holiday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Holiday"))
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] = 1

    if apply_shifts:
        profiles_weekday, profiles_saturday, profiles_sunday, profiles_holiday = (
            module_work_shift.apply_work_shifts(
                profiles_weekday,
                profiles_saturday,
                profiles_sunday,
                profiles_holiday,
                shift_type=2,
                family="continuous",
                betas={
                    "Continuous mechanical drive": 0.85,
                    "Discontinuous mechanical drive": 0.85,
                    "Mechanical drives": 0.85,
                    "Lighting": 0.7,
                    "ICT": 0.3,
                    "Process heat": 0.2,
                    "Process cooling": 0.1,
                    "Space heating": 0.3,
                    "Space cooling": 0.3,
                    "Hot water": 0.2,
                },
                ramp_minutes=(45, 45),
                rescale=True,
            )
        )

    """ INPUT: INDUSTRY DATA """
    project_root = _resolve_project_root(base_path)
    all_info_path = _resolve_existing_path(
        [
            project_root / "Data" / "ElectricalSpecific" / "All_info_industry_types_electrical.xlsx",
            project_root / "ElectricalProfile" / "data" / "All_info_industry_types_electrical.xlsx",
            project_root / "Electrical" / "All_info_industry_types_electrical.xlsx",
        ]
    )
    industry_info_df = pd.read_excel(all_info_path)
    industry_info_df.dropna(how="all", axis=0, inplace=True)
    industry_info_df.dropna(how="all", axis=1, inplace=True)
    industry_info_df.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = industry_info_df[industry_info_df.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    # Rename Mechanical drive -> Mechanical drives
    if "Mechanical drives" not in data_industry_type.columns and "Mechanical drive" in data_industry_type.columns:
        data_industry_type = data_industry_type.rename(columns={"Mechanical drive": "Mechanical drives"})

    weight_columns = [
        "Space heating",
        "Hot water",
        "Process heat",
        "Space cooling",
        "Process cooling",
        "Lighting",
        "ICT",
    ]
    mech_col = None
    if "Mechanical drives" in data_industry_type.columns:
        mech_col = "Mechanical drives"
    elif "Mechanical drive" in data_industry_type.columns:
        mech_col = "Mechanical drive"
    if mech_col:
        weight_columns.append(mech_col)

    weights = data_industry_type[weight_columns].iloc[0].astype(float)

    has_cont = "Continuous mechanical drive" in profiles_weekday.columns
    has_disc = "Discontinuous mechanical drive" in profiles_weekday.columns
    if mech_col and (has_cont or has_disc) and mech_col in weights.index:
        mech_total = float(weights[mech_col])
        weights = weights.drop(labels=[mech_col])
        if has_cont and has_disc:
            cont_sum = float(profiles_weekday["Continuous mechanical drive"].sum())
            disc_sum = float(profiles_weekday["Discontinuous mechanical drive"].sum())
            denom = cont_sum + disc_sum
            if denom > 0:
                cont_ratio = cont_sum / denom
                disc_ratio = disc_sum / denom
            else:
                cont_ratio = 0.5
                disc_ratio = 0.5
        elif has_cont:
            cont_ratio = 1.0
            disc_ratio = 0.0
        else:
            cont_ratio = 0.0
            disc_ratio = 1.0

        if has_cont:
            weights["Continuous mechanical drive"] = mech_total * cont_ratio
        if has_disc:
            weights["Discontinuous mechanical drive"] = mech_total * disc_ratio

    weights = weights.reindex(profiles_weekday.columns)
 

    """ CREATE DAILY PROFILES """
    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type 
   
   
    
def build_thermal_daily_profiles(industry_number, base_path, apply_shifts=True):
    """ INPUT: END USER PROFILES """
    project_root = _resolve_project_root(base_path)
    thermal_data_path = _resolve_existing_path(
        [
            project_root / "Data" / "HeatSpecific" / "Load_profiles_daytypes.xlsx",
            project_root / "ThermalProfile" / "data" / "Load_profiles_daytypes.xlsx",
            project_root / "Thermal" / "Load_profiles_daytypes.xlsx",
        ]
    )
    profiles_weekday = pd.read_excel(thermal_data_path, sheet_name="Week_day", index_col=0)
    profiles_saturday = pd.read_excel(thermal_data_path, sheet_name="Saturday", index_col=0) 
    profiles_sunday = pd.read_excel(thermal_data_path, sheet_name="Sunday", index_col=0)
    profiles_holiday = pd.read_excel(thermal_data_path, sheet_name="Holiday", index_col=0)
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] =1
    
    
    """ INPUT: INDUSTRY DATA """
    all_info_path = _resolve_existing_path(
        [
            project_root / "Data" / "HeatSpecific" / "All_info_industry_types_thermal.xlsx",
            project_root / "ThermalProfile" / "data" / "All_info_industry_types_thermal.xlsx",
            project_root / "Thermal" / "All_info_industry_types_thermal.xlsx",
        ]
    )
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
