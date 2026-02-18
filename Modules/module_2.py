import pandas as pd
import numpy as np



def _adjust_total(total, factor, ref_idx=0, base=100):
    """
    Shift a total series by a reference index, scale by factor, and add base.
    """
    y = total - total.iloc[ref_idx]
    return y * factor + base


def _redistribute(profile, new_total):
    """
    Redistribute adjusted total across application shares and round results.
    """
    shares = profile.div(profile["Total"], axis=0)
    out = shares.mul(new_total, axis=0)
    return out.round(2)


def _resolve_factor_column(data_industry_type, candidates):
    for name in candidates:
        if name in data_industry_type.columns:
            return name
    raise KeyError(f"None of the factor columns found: {', '.join(candidates)}")



def apply_peak_base_factors(year, industry_number, data_industry_type, 
                            weekday_1, saturday_1, sunday_1, holiday_1, constant_1):
    """
    Adjust daily profiles with peak/base factors and redistribute by shares.

    General steps applied to each day type:
    Step 1: build a relative total series by shifting the total to start at a reference timestep.
    Step 2: compute the relevant extrema from that shifted series (peak or base).
    Step 3: read the target factor from industry data and fall back to the actual value if missing.
    Step 4: rescale the total series with the selected factor and add the base level.
    Step 5: redistribute the adjusted total across applications using their original shares.

    Concrete adjustments:
    Weekday uses Peak_factor and centers at the first timestep.
    Saturday uses Base_factor and centers at the first timestep.
    Sunday uses Base_factor and centers at timestep 95.
    Holiday uses Base_factor and centers at the first timestep.
    Constant sets the total to 100 + Base_factor for all timesteps. This method differs from others 
    because the distribution of applications remains the same at every time point (constant proportions).
    """

    """ WEEK DAY ADJUSTMENT """
    # Step 1:
    y = weekday_1["Total"] - weekday_1["Total"].iloc[0]
    
    # Step 2:
    peak_actual = np.max(y)

    # Step 3:
    peak_col = _resolve_factor_column(data_industry_type, ["Peak_factor", "Peak_faktor"])
    peak_target = (float(data_industry_type[data_industry_type["industry_number"] == industry_number][peak_col].iloc[0]) - 1) * 100
    if peak_target == -100: 
        peak_target = peak_actual
    
    # Step 4:
    weekday = _adjust_total(weekday_1["Total"], peak_target / peak_actual)

    # Step 5:
    weekday_adjusted = _redistribute(weekday_1, weekday)


    """ SATURDAY ADJUSTMENT """
    y = saturday_1["Total"] - saturday_1["Total"].iloc[0]
    base_actual = np.min(y)
    base_col = _resolve_factor_column(data_industry_type, ["Base_factor", "Base_faktor"])
    base_target = (float(data_industry_type[data_industry_type["industry_number"] == industry_number][base_col].iloc[0]) - 1) * 100
    if base_target == -100:
        base_target = base_actual
    saturday = _adjust_total(saturday_1["Total"], base_target / base_actual)
    saturday_adjusted = _redistribute(saturday_1, saturday)


    """ SUNDAY ADJUSTMENT """
    sunday = _adjust_total(sunday_1["Total"], base_target / base_actual, ref_idx=95)
    sunday_adjusted = _redistribute(sunday_1, sunday)


    """ HOLIDAY ADJUSTMENT """
    holiday = _adjust_total(holiday_1["Total"], base_target / base_actual)
    holiday_adjusted = _redistribute(holiday_1, holiday)


    """ CONSTANT LOAD ADJUSTMENT """
    constant = pd.Series([100 + base_target] * len(constant_1), index=constant_1.index)
    constant_adjusted = _redistribute(constant_1, constant)
    
    return weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted
