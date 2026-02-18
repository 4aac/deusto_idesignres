import pandas as pd
from pathlib import Path



def _resolve_project_root(base_path):
    if base_path:
        path = Path(base_path)
    else:
        path = Path(__file__).resolve().parent.parent

    name = path.name.lower()
    if name in {"electricalprofile", "thermalprofile"}:
        return path.parent
    if name == "data" and path.parent.name.lower() in {"electricalprofile", "thermalprofile"}:
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

    if "Continuous mechanical drive" in df.columns or "Discontinuous mechanical drive" in df.columns:
        cont = df["Continuous mechanical drive"] if "Continuous mechanical drive" in df.columns else 0
        disc = df["Discontinuous mechanical drive"] if "Discontinuous mechanical drive" in df.columns else 0
        df["Mechanical drives"] = cont + disc
        df = df.drop(columns=[c for c in ["Continuous mechanical drive", "Discontinuous mechanical drive"] if c in df.columns])

    if "Mechanical drive" in df.columns and "Mechanical drives" not in df.columns:
        df = df.rename(columns={"Mechanical drive": "Mechanical drives"})

    return df


def _select_electric_weights(data_industry_type):
    if "Mechanical drives" not in data_industry_type.columns and "Mechanical drive" in data_industry_type.columns:
        data_industry_type = data_industry_type.rename(columns={"Mechanical drive": "Mechanical drives"})

    weights = data_industry_type[
        [
            "Space heating",
            "Hot water",
            "Process heat",
            "Space cooling",
            "Process cooling",
            "Lighting",
            "ICT",
            "Mechanical drives",
        ]
    ].iloc[0].astype(float)
    return weights



def build_electric_daily_profiles(industry_number, base_path):
    """ INPUT: END USER PROFILES """
    profiles_weekday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Week_day"))
    profiles_saturday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Saturday"))
    profiles_sunday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Sunday"))
    profiles_holiday = _normalize_electric_profile_columns(_read_enduser_profiles(base_path, "Holiday"))
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] = 1


    """ INPUT: INDUSTRY DATA """
    project_root = _resolve_project_root(base_path)
    all_info_path = _resolve_existing_path(
        [
            project_root / "ElectricalProfile" / "data" / "All_info_industry_types_electrical.xlsx",
            project_root / "Electrical" / "All_info_industry_types_electrical.xlsx",
        ]
    )
    all_info_wz = pd.read_excel(all_info_path)
    all_info_wz.dropna(how="all", axis=0, inplace=True)
    all_info_wz.dropna(how="all", axis=1, inplace=True)
    all_info_wz.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = all_info_wz[all_info_wz.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    weights = _select_electric_weights(data_industry_type)
 

    """ CREATE DAILY PROFILES """
    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type 
   
   
    
def build_thermal_daily_profiles(industry_number, base_path):
    """ INPUT: END USER PROFILES """
    project_root = _resolve_project_root(base_path)
    thermal_data_path = _resolve_existing_path(
        [
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
            project_root / "ThermalProfile" / "data" / "All_info_industry_types_thermal.xlsx",
            project_root / "Thermal" / "All_info_industry_types_thermal.xlsx",
        ]
    )
    all_info_wz = pd.read_excel(all_info_path)
    all_info_wz.dropna(how="all",axis=0, inplace=True)
    all_info_wz.dropna(how="all",axis=1, inplace=True)
    all_info_wz.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = all_info_wz[all_info_wz.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
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
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type
