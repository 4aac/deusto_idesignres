import numpy as np



def upscale_yearly(year, industry_number, df_normalized, data_industry_type):
    """
    Scale the normalized annual profile to the industry's actual yearly consumption.
    """
    # Get actual energy consumption for this industry and year
    energy_per_year_MWh = float(data_industry_type["Energy consumption " + str(year)].iloc[0])
    
    # Scale the normalized profile to actual consumption
    df_scaled = df_normalized * energy_per_year_MWh
    
    # Round to whole kilowatts
    df_scaled = df_scaled.round(0)
    
    return df_scaled



def add_fluctuations(industry_number, df_scaled, data_industry_type):
    """
    Add realistic fluctuations to mechanical drives.
    """
    # Get fluctuation factor from industry data (relative to 100 kW baseline)
    s_norm = data_industry_type["Fluctuation"][industry_number]
    
    # Find actual peak power in the load profile
    power_peak = np.max(df_scaled["Total"])
    
    # Scale the fluctuation to actual power level
    s_rel = s_norm * (100 / power_peak) ** 0.5
    
    # Convert relative fluctuation (%) to absolute value (kW)
    s_abs = s_rel / 100 * power_peak
    
    # Generate noise
    rand_numbers = np.random.normal(0, s_abs, len(df_scaled)).round(0)
    
    # Add fluctuations to mechanical drives and recalculate total
    df_scaled["Mechanical drives"] = df_scaled["Mechanical drives"] + rand_numbers
    df_scaled["Total"] = df_scaled["Total"] + rand_numbers
    
    return df_scaled
