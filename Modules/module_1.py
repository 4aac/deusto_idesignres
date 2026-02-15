import pandas as pd
from pathlib import Path



def _read_enduser_profiles(path, sheet_name):
    """
    Read an end-user profile sheet and drop empty rows.
    """
    df = pd.read_excel(
        path + "\\Electrical\\Load_profiles_enduser.xlsx",
        index_col=0,
        sheet_name=sheet_name,
    )
    df = df.dropna(axis=0)
    return df


def _apply_profile_weights(profiles, weights):
    """
    Multiply profiles by column weights and add a total column.
    """
    y = profiles.mul(weights, axis=1)  # Application profiles * Share of applications
    y["Total"] = y.sum(axis=1)
    return y



def build_electric_daily_profiles(industry_number, PATH):
    """ INPUT: END USER PROFILES """
    profiles_weekday = _read_enduser_profiles(PATH, "Week_day")
    profiles_saturday = _read_enduser_profiles(PATH, "Saturday")
    profiles_sunday = _read_enduser_profiles(PATH, "Sunday")
    profiles_holiday = _read_enduser_profiles(PATH, "Holiday")
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] = 1


    """ INPUT: INDUSTRY DATA """
    all_info_wz = pd.read_excel(PATH + "\\Electrical\\All_info_industry_types_electrical.xlsx".format()) 
    all_info_wz.dropna(how="all", axis=0, inplace=True)
    all_info_wz.dropna(how="all", axis=1, inplace=True)
    all_info_wz.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = all_info_wz[all_info_wz.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    weights = data_industry_type[
        ["Space heating", "Hot water", "Process heat", "Space cooling", 
         "Process cooling", "Lighting", "ICT", "Mechanical drives"]
    ].iloc[0].astype(float)
 

    """ CREATE DAILY PROFILES """
    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type 
   
   
    
def build_thermal_daily_profiles(industry_number, PATH):
    """ INPUT: END USER PROFILES """
    base_path = Path(PATH)
    profiles_weekday = pd.read_excel(base_path / "Thermal" / "Load_profiles_daytypes.xlsx", sheet_name="Week_day", index_col=0)
    profiles_saturday = pd.read_excel(base_path / "Thermal" / "Load_profiles_daytypes.xlsx", sheet_name="Saturday", index_col=0) 
    profiles_sunday = pd.read_excel(base_path / "Thermal" / "Load_profiles_daytypes.xlsx", sheet_name="Sunday", index_col=0)
    profiles_holiday = pd.read_excel(base_path / "Thermal" / "Load_profiles_daytypes.xlsx", sheet_name="Holiday", index_col=0)
    
    profiles_constant = profiles_weekday.copy()
    profiles_constant.loc[:,:] =1
    
    
    """ INPUT: INDUSTRY DATA """
    all_info_wz = pd.read_excel(base_path / "Thermal" / "All_info_industry_types_thermal.xlsx") 
    all_info_wz.dropna(how="all",axis=0, inplace=True)
    all_info_wz.dropna(how="all",axis=1, inplace=True)
    all_info_wz.fillna(0, inplace=True)
    

    """ SELECT DATA FROM THE CHOSEN INDUSTRY """
    data_industry_type = all_info_wz[all_info_wz.industry_number.eq(industry_number)]  # Filters rows with specific industry_wz
    data_industry = data_industry_type.iloc[:, 3:9]  # Extracts temperature range values
    data_industry = data_industry.astype(float)


    """ CREATE DAILY PROFILES """   
    weights = data_industry.iloc[0]

    weekday_profiles = _apply_profile_weights(profiles_weekday, weights)
    saturday_profiles = _apply_profile_weights(profiles_saturday, weights)
    sunday_profiles = _apply_profile_weights(profiles_sunday, weights)
    holiday_profiles = _apply_profile_weights(profiles_holiday, weights)
    constant_profiles = _apply_profile_weights(profiles_constant, weights)
    
    return weekday_profiles, saturday_profiles, sunday_profiles, holiday_profiles, constant_profiles, data_industry_type
