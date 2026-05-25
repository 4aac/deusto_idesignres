import numpy as np
import pandas as pd


DEFAULT_SHIFT_SCHEDULES = {
    "weekday": {
        1: (8, 16),
        2: (6, 22),
        3: (0, 24)
    },
    "saturday": {
        1: (8, 14),
        2: (6, 14),
        3: (0, 24)
    },
    "sunday": {
        1: None,
        2: None,
        3: (0, 24)
    },
    "holiday": {
        1: None,
        2: None,
        3: (0, 24)
    },
}

DEFAULT_FAMILY_SETTINGS = {
    "continuous": {
        "ramp_up": 120,
        "ramp_down": 120,
        "betas": {
            "Process heat": 0.3,
            "Continuous mechanical drive": 0.4,
            "Discontinuous mechanical drive": 0.4,
            "Mechanical drive": 0.4,
            "Space heating": 0.3,
            "Hot water": 0.3,
            "Space cooling": 0.3,
            "Process cooling": 0.1,
            "Lighting": 0.4,
            "ICT": 0.2,
        },
    },
    "batch": {
        "ramp_up": 30,
        "ramp_down": 30,
        "betas": {
            "Process heat": 0.9,
            "Continuous mechanical drive": 0.85,
            "Discontinuous mechanical drive": 0.85,
            "Mechanical drive": 0.85,
            "Space heating": 0.4,
            "Hot water": 0.5,
            "Space cooling": 0.5,
            "Process cooling": 0.2,
            "Lighting": 0.6,
            "ICT": 0.3,
        },
    },
    "assembly": {
        "ramp_up": 60,
        "ramp_down": 60,
        "betas": {
            "Process heat": 0.8,
            "Continuous mechanical drive": 0.9,
            "Discontinuous mechanical drive": 0.9,
            "Mechanical drive": 0.9,
            "Space heating": 0.5,
            "Hot water": 0.5,
            "Space cooling": 0.7,
            "Process cooling": 0.1,
            "Lighting": 0.8,
            "ICT": 0.4,
        },
    },
}


def _build_activity_curve(n_steps, work_window, ramp_up, ramp_down):
    """
    Build a daily activity curve from a work window and ramp durations.
    """
    # No work window means no scheduled activity for this day type.
    if work_window is None:
        return np.zeros(n_steps, dtype=float)

    # Convert the work window from hours to minutes within the day.
    start_hour, end_hour = work_window
    start_minute = float(start_hour) * 60
    end_minute = float(end_hour) * 60

    # A full-day window is already constant activity.
    if start_minute <= 0 and end_minute >= 24 * 60:
        return np.ones(n_steps, dtype=float)

    # Build one value per profile row, assuming the profile covers one day.
    step_minutes = 24 * 60 / n_steps
    minutes = np.arange(n_steps) * step_minutes
    activity = np.zeros(n_steps, dtype=float)

    # Clamp ramps so they never extend outside the day boundaries.
    ramp_up = max(0.0, min(float(ramp_up), start_minute))
    ramp_down = max(0.0, min(float(ramp_down), 24 * 60 - end_minute))

    for i, minute in enumerate(minutes):
        # Ramp up linearly before the shift starts.
        if ramp_up > 0 and (start_minute - ramp_up) <= minute < start_minute:
            activity[i] = (minute - (start_minute - ramp_up)) / ramp_up
        # During the shift, activity is fully on.
        elif start_minute <= minute < end_minute:
            activity[i] = 1.0
        # Ramp down linearly after the shift ends.
        elif ramp_down > 0 and end_minute <= minute < (end_minute + ramp_down):
            activity[i] = 1.0 - (minute - end_minute) / ramp_down

    return activity


def _apply_shift_to_day(profile, day_type, shift_type, beta_map, ramp_up, ramp_down, schedules, rescale):
    """
    Apply the configured shift activity curve to one day-type profile.
    """
    if profile is None:
        return None
    if not isinstance(profile, pd.DataFrame):
        raise TypeError("Profiles must be pandas DataFrames.")

    shifted_profile = profile.copy()
    if shifted_profile.empty:
        return shifted_profile

    # Select the configured work window for this day type and shift pattern.
    work_window = schedules.get(day_type, {}).get(shift_type)
    activity = _build_activity_curve(len(shifted_profile), work_window, ramp_up, ramp_down)
    application_columns = [column for column in shifted_profile.columns if column != "Total"]

    for column in application_columns:
        # Beta controls how much this end use follows the activity curve.
        beta = float(beta_map.get(column, 0.0))
        multiplier = (1.0 - beta) + beta * activity
        adjusted_values = shifted_profile[column].astype(float).to_numpy() * multiplier

        if rescale:
            # Preserve the original daily energy after reshaping the profile.
            original_sum = float(shifted_profile[column].sum())
            adjusted_sum = float(adjusted_values.sum())
            if adjusted_sum > 0:
                adjusted_values = adjusted_values * (original_sum / adjusted_sum)

        shifted_profile[column] = adjusted_values

    if "Total" in shifted_profile.columns:
        # Recompute Total from the adjusted application columns.
        shifted_profile["Total"] = shifted_profile[application_columns].sum(axis=1)

    return shifted_profile


def apply_work_shifts(
    profiles_weekday,
    profiles_saturday,
    profiles_sunday,
    profiles_holiday,
    shift_type=2,
    family="assembly",
    betas=None,
    ramp_minutes=None,
    rescale=True,
    schedule_by_day=None,
):
    """
    Apply a work-shift activity mask to weekday, Saturday, Sunday and holiday profiles.

    Beta controls how strongly each application follows the shift schedule:
    0.0 keeps the original shape, 1.0 fully follows the activity curve.
    """
    try:
        shift_type = int(shift_type)
    except (TypeError, ValueError):
        shift_type = 2
    if shift_type not in (1, 2, 3):
        shift_type = 2

    family_key = str(family).strip().lower()
    if family_key not in DEFAULT_FAMILY_SETTINGS:
        family_key = "assembly"

    default_settings = DEFAULT_FAMILY_SETTINGS[family_key]
    beta_map = dict(default_settings["betas"])
    if betas:
        beta_map.update(betas)

    if ramp_minutes is None:
        ramp_up = float(default_settings["ramp_up"])
        ramp_down = float(default_settings["ramp_down"])
    elif isinstance(ramp_minutes, (list, tuple)) and len(ramp_minutes) == 2:
        ramp_up = float(ramp_minutes[0])
        ramp_down = float(ramp_minutes[1])
    else:
        ramp_up = float(ramp_minutes)
        ramp_down = float(ramp_minutes)

    schedules = schedule_by_day if schedule_by_day is not None else DEFAULT_SHIFT_SCHEDULES

    shifted_profiles = []
    for day_type, profile in {
        "weekday": profiles_weekday,
        "saturday": profiles_saturday,
        "sunday": profiles_sunday,
        "holiday": profiles_holiday,
    }.items():
        shifted_profiles.append(
            _apply_shift_to_day(
                profile=profile,
                day_type=day_type,
                shift_type=shift_type,
                beta_map=beta_map,
                ramp_up=ramp_up,
                ramp_down=ramp_down,
                schedules=schedules,
                rescale=rescale,
            )
        )

    return tuple(shifted_profiles)
