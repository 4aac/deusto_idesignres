
import numpy as np
import pandas as pd


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
    Apply a simple work-shift activity mask to end-use daily profiles.

    Inputs:
    - profiles_weekday/profiles_saturday/profiles_sunday/profiles_holiday:
      pandas DataFrames with a daily profile per end-use (columns). Rows are
      time steps across 24 hours. If a "Total" column exists, it will be
      recomputed after applying the shift mask.
    - shift_type: integer shift pattern selector (1, 2, or 3) used to pick
      a time window from schedule_by_day (e.g., 1=single shift, 2=two shifts,
      3=continuous; exact windows depend on schedule_by_day).
    - family: industrial family key that selects default betas and ramp
      durations. Supported defaults: "continuous", "batch", "assembly".
    - betas: optional dict mapping end-use name -> beta in [0, 1], overriding
      defaults for the chosen family.
    - ramp_minutes: optional ramp duration(s) in minutes. If a single number,
      it is used for both ramp-up and ramp-down. If a (up, down) tuple/list,
      they are used separately.
    - rescale: if True, preserve daily energy by rescaling each adjusted
      end-use profile to its original daily sum.
    - schedule_by_day: optional dict with per-day shift windows by shift_type,
      e.g. {"weekday": {1: (8, 16), 2: (6, 22), 3: (0, 24)}, ...}.

    Core idea:
    - Build an activity curve A(t) in [0, 1] from a shift schedule with ramps.
    - For each end-use u, apply: m_u(t) = (1 - beta_u) + beta_u * A(t)
    - Multiply the base profile by m_u(t). Optionally re-scale to keep daily energy.
    """
    # ====== DEFAULT VALUES =======
    # Get family
    family_key = str(family).strip().lower()

    family_defaults = {
        "continuous": {
            "ramp_up": 120,
            "ramp_down": 120,
            "betas": {
                "Process heat": 0.3,
                "Mechanical drives": 0.4,
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
                "Mechanical drives": 0.85,
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
                "Mechanical drives": 0.9,
                "Space heating": 0.5,
                "Hot water": 0.5,
                "Space cooling": 0.7,
                "Process cooling": 0.1,
                "Lighting": 0.8,
                "ICT": 0.4,
            },
        },
    }
    if family_key not in family_defaults:
        family_key = "assembly"

    # Get betas
    defaults = family_defaults[family_key]
    beta_map = dict(defaults["betas"])
    if betas: beta_map.update(betas)

    # Get ramps
    # ramp_minutes can be a single number or a (ramp_up, ramp_down) pair
    if ramp_minutes is None:
        ramp_up = defaults["ramp_up"]
        ramp_down = defaults["ramp_down"]
    else:
        if isinstance(ramp_minutes, (list, tuple)) and len(ramp_minutes) == 2:
            ramp_up, ramp_down = float(ramp_minutes[0]), float(ramp_minutes[1])
        else:
            ramp_up = float(ramp_minutes)
            ramp_down = float(ramp_minutes)

    # Default shift schedules
    if schedule_by_day is None:
        schedule_by_day = {
            "weekday": {1: (8, 16), 2: (6, 22), 3: (0, 24)},
            "saturday": {1: (8, 14), 2: (6, 14), 3: (0, 24)},
            "sunday": {1: None, 2: None, 3: (0, 24)},
            "holiday": {1: None, 2: None, 3: (0, 24)},
        }

    # Normalize shift type
    try:
        shift_type = int(shift_type)
    except ValueError:
        shift_type = 2
    if shift_type not in (1, 2, 3):
        shift_type = 2


    def _apply_to_day(profile_df, day_key):
        """
        Apply the day-specific shift activity mask to a single daily profile.
        """
        if profile_df is None:
            return None
        if not isinstance(profile_df, pd.DataFrame):
            raise TypeError("Profiles must be pandas DataFrames.")

        out = profile_df.copy()

        """ ACTIVITY CURVE A(t) """
        # Build an activity vector in [0, 1] based on the daily time window
        # and ramp-up/ramp-down durations.
        n_steps = len(out)
        if n_steps == 0:
            return out
        step_minutes = 24 * 60 / n_steps
        minutes = np.arange(n_steps) * step_minutes

        schedule = schedule_by_day.get(day_key, {})
        window = schedule.get(shift_type, None)

        if window is None:
            # No shift active for this day/shift_type
            activity = np.zeros(n_steps, dtype=float)
        else:
            start_h, end_h = window
            start = float(start_h) * 60
            end = float(end_h) * 60

            if start <= 0 and end >= 24 * 60:
                # Full-day operation
                activity = np.ones(n_steps, dtype=float)
            else:
                # Clamp ramp durations to day bounds
                ramp_up_eff = max(0.0, min(ramp_up, start))
                ramp_down_eff = max(0.0, min(ramp_down, 24 * 60 - end))

                activity = np.zeros(n_steps, dtype=float)
                for i, t in enumerate(minutes):
                    if ramp_up_eff > 0 and (start - ramp_up_eff) <= t < start:
                        # Ramp-up segment
                        activity[i] = (t - (start - ramp_up_eff)) / ramp_up_eff
                    elif start <= t < end:
                        # Fully active shift
                        activity[i] = 1.0
                    elif ramp_down_eff > 0 and end <= t < (end + ramp_down_eff):
                        # Ramp-down segment
                        activity[i] = 1.0 - (t - end) / ramp_down_eff
                    else:
                        # Outside shift window
                        activity[i] = 0.0

        """ APPLY BETA """
        # Each end-use is a blend of baseline (1-beta) and shift activity (beta)
        cols = [c for c in out.columns if c != "Total"]
        for col in cols:
            key = col
            if key == "Mechanical drive":
                # Normalize known alternate label
                key = "Mechanical drives"
            beta = float(beta_map.get(key, 0.0))
            multiplier = (1.0 - beta) + beta * activity
            adjusted = out[col].astype(float).values * multiplier
            if rescale:
                # Keep daily energy constant after applying the mask
                original_sum = float(np.sum(out[col].values))
                adjusted_sum = float(np.sum(adjusted))
                if adjusted_sum > 0:
                    adjusted = adjusted * (original_sum / adjusted_sum)
            out[col] = adjusted

        if "Total" in out.columns:
            # Recompute Total after all end-uses are adjusted
            out["Total"] = out[cols].sum(axis=1)
        return out

    # Apply shift adjustment to each day-type profile
    weekday_adj = _apply_to_day(profiles_weekday, "weekday")
    saturday_adj = _apply_to_day(profiles_saturday, "saturday")
    sunday_adj = _apply_to_day(profiles_sunday, "sunday")
    holiday_adj = _apply_to_day(profiles_holiday, "holiday")

    return weekday_adj, saturday_adj, sunday_adj, holiday_adj
