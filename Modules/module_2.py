import pandas as pd
import numpy as np


EPSILON = 1e-9


def _get_factor(data_industry_type, industry_number, column):
    """
    Read a positive peak/base factor. Zero or missing values mean no external factor is available.
    """
    row = data_industry_type[data_industry_type["industry_number"] == industry_number]
    if row.empty or column not in row.columns:
        return None

    value = pd.to_numeric(row[column], errors="coerce").iloc[0]
    if pd.isna(value) or float(value) <= 0:
        return None

    return float(value)


def _relative_delta(total, ref_idx=0, mode="min"):
    """
    Return the peak or base delta relative to a reference timestep.
    """
    relative = total.astype(float) - float(total.iloc[ref_idx])
    return float(relative.max() if mode == "max" else relative.min())


def _adjust_total(total, target_delta, ref_idx=0, base=100, mode="min"):
    """
    Shift a total series by a reference index, scale it to a target delta, and keep it non-negative.
    """
    relative = total.astype(float) - float(total.iloc[ref_idx])
    actual_delta = float(relative.max() if mode == "max" else relative.min())

    if abs(actual_delta) < EPSILON:
        adjusted = pd.Series(base + target_delta, index=total.index, dtype=float)
    else:
        adjusted = relative * (target_delta / actual_delta) + base

    return adjusted.clip(lower=0.0)


def _redistribute(profile, new_total):
    """
    Redistribute adjusted total across application shares, preserving non-negative values.
    """
    application_columns = [column for column in profile.columns if column != "Total"]
    denominator = profile["Total"].replace(0, np.nan)
    shares = profile[application_columns].div(denominator, axis=0)

    zero_total_rows = denominator.isna()
    if zero_total_rows.any() and application_columns:
        shares.loc[zero_total_rows, :] = 1.0 / len(application_columns)

    out = shares.fillna(0.0).mul(new_total.clip(lower=0.0), axis=0)
    out = out.clip(lower=0.0).round(2)
    out["Total"] = out[application_columns].sum(axis=1).round(2)
    return out


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
    peak_factor = _get_factor(data_industry_type, industry_number, "Peak_factor")
    peak_target = (
        (peak_factor - 1.0) * 100.0
        if peak_factor is not None
        else _relative_delta(weekday_1["Total"], mode="max")
    )
    weekday = _adjust_total(weekday_1["Total"], peak_target, mode="max")
    weekday_adjusted = _redistribute(weekday_1, weekday)


    """ SATURDAY ADJUSTMENT """
    base_factor = _get_factor(data_industry_type, industry_number, "Base_factor")
    saturday_base_target = (
        (base_factor - 1.0) * 100.0
        if base_factor is not None
        else _relative_delta(saturday_1["Total"], mode="min")
    )
    saturday = _adjust_total(saturday_1["Total"], saturday_base_target, mode="min")
    saturday_adjusted = _redistribute(saturday_1, saturday)


    """ SUNDAY ADJUSTMENT """
    sunday_base_target = (
        (base_factor - 1.0) * 100.0
        if base_factor is not None
        else _relative_delta(sunday_1["Total"], ref_idx=95, mode="min")
    )
    sunday = _adjust_total(sunday_1["Total"], sunday_base_target, ref_idx=95, mode="min")
    sunday_adjusted = _redistribute(sunday_1, sunday)


    """ HOLIDAY ADJUSTMENT """
    holiday_base_target = (
        (base_factor - 1.0) * 100.0
        if base_factor is not None
        else _relative_delta(holiday_1["Total"], mode="min")
    )
    holiday = _adjust_total(holiday_1["Total"], holiday_base_target, mode="min")
    holiday_adjusted = _redistribute(holiday_1, holiday)


    """ CONSTANT LOAD ADJUSTMENT """
    constant_level = (
        base_factor * 100.0
        if base_factor is not None
        else 100.0 + saturday_base_target
    )
    constant = pd.Series(
        [max(constant_level, 0.0)] * len(constant_1),
        index=constant_1.index,
    )
    constant_adjusted = _redistribute(constant_1, constant)
    
    return weekday_adjusted, saturday_adjusted, sunday_adjusted, holiday_adjusted, constant_adjusted
