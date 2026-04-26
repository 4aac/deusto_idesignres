import numpy as np


def upscale_yearly(year, industry_number, df_normalized, data_industry_type):
    """
    Scale the normalized annual profile to the industry's actual yearly consumption.
    """
    # Get actual energy consumption for this industry and year
    energy_col_en = f"Energy consumption {year}"
    energy_col_de = f"Energieverbrauch {year}"
    energy_col = energy_col_en if energy_col_en in data_industry_type.columns else energy_col_de
    energy_per_year_MWh = float(data_industry_type[energy_col].iloc[0])
    
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
    
    has_cont = "Continuous mechanical drive" in df_scaled.columns
    has_disc = "Discontinuous mechanical drive" in df_scaled.columns

    if has_cont or has_disc:
        if has_cont and has_disc:
            total_mech = df_scaled["Continuous mechanical drive"] + df_scaled["Discontinuous mechanical drive"]
            ratio_cont = total_mech.copy()
            ratio_cont[total_mech > 0] = df_scaled["Continuous mechanical drive"][total_mech > 0] / total_mech[total_mech > 0]
            ratio_cont[total_mech <= 0] = 0.5
            ratio_disc = 1.0 - ratio_cont

            df_scaled["Continuous mechanical drive"] = (
                df_scaled["Continuous mechanical drive"] + rand_numbers * ratio_cont
            )
            df_scaled["Discontinuous mechanical drive"] = (
                df_scaled["Discontinuous mechanical drive"] + rand_numbers * ratio_disc
            )
        else:
            target_col = "Continuous mechanical drive" if has_cont else "Discontinuous mechanical drive"
            df_scaled[target_col] = df_scaled[target_col] + rand_numbers

        df_scaled["Total"] = df_scaled["Total"] + rand_numbers
        return df_scaled

    # New 6-category structure
    if "Motor drives" in df_scaled.columns:
        df_scaled["Motor drives"] = df_scaled["Motor drives"] + rand_numbers
        df_scaled["Total"] = df_scaled["Total"] + rand_numbers
        return df_scaled

    # Fallback to aggregated mechanical drives
    if "Mechanical drives" in df_scaled.columns:
        df_scaled["Mechanical drives"] = df_scaled["Mechanical drives"] + rand_numbers
        df_scaled["Total"] = df_scaled["Total"] + rand_numbers

    return df_scaled
