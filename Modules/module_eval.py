from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import r2_score

BASE_PATH = Path(__file__).resolve().parents[1]
MATLAB_PROFILE = BASE_PATH / "Helpers" / "regression_load_profiles" / "Perfil_MATLAB.csv"
PYTHON_PROFILE = (
    BASE_PATH
    / "Generated"
    / "load_profiles"
    / "iDesign_RES_Iron and steel_ISI-DE.xlsx"
)


def _normalize_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """
    Normalize a profile by its annual total energy.
    """
    total = np.sum(values)
    if total == 0:
        raise ValueError(f"{profile_name} cannot be normalized because its sum is 0.")
    return values / total


def _shift_to_time(shift: int, minutes_per_sample: int = 15) -> str:
    """
    Convert a sample shift into a readable time offset.
    """
    total_minutes = abs(shift) * minutes_per_sample
    hours, minutes = divmod(total_minutes, 60)
    sign = "-" if shift < 0 else "+"
    return f"{sign}{hours} h {minutes} min"


def _best_shift_r2(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    max_shift: int,
    predictors: int = 5,
) -> tuple[float, float, int]:
    """Find the temporal shift that gives the highest R2.

    Parameters
    ----------
    y_true:
        Reference profile.
    y_pred:
        Profile to shift and evaluate.
    max_shift:
        Maximum number of samples to shift in both directions. With 15-minute
        samples, 672 means one week.
    predictors:
        Number of predictors used for adjusted R2.

    Returns
    -------
    tuple[float, float, int]
        Best R2, best adjusted R2 and the shift that produced them.

    How to use
    ----------
    Use this when the profiles may be temporally misaligned. A much higher R2
    after shifting suggests a calendar or timestamp alignment issue.
    """

    best_r2 = -np.inf
    best_r2_corr = -np.inf
    best_shift = 0

    # np.roll applies a circular shift: values leaving one side enter again on
    # the other side. This is useful for annual profiles where the period wraps.
    for shift in range(-max_shift, max_shift + 1):
        shifted_y_pred = np.roll(y_pred, shift)
        r2, r2_corr = calculate_determination_coefficients(
            y_true,
            shifted_y_pred,
            predictors,
        )
        if r2 > best_r2:
            best_r2 = r2
            best_r2_corr = r2_corr
            best_shift = shift

    return best_r2, best_r2_corr, best_shift


""" Scores """

def _r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate the standard coefficient of determination.

    Parameters
    ----------
    y_true:
        Reference values. In this module, this is the MATLAB profile.
    y_pred:
        Values to evaluate. In this module, this is the generated Python
        profile.

    Returns
    -------
    float
        R2 score. A value close to 1 means high similarity. Values below 0 are
        possible when the prediction is worse than using the mean of y_true.

    Notes
    -----
    The function uses ``sklearn.metrics.r2_score`` when available. If sklearn is
    not installed, it applies the mathematical definition directly.
    """

    if r2_score is not None:
        return float(r2_score(y_true, y_pred))

    # Fallback implementation:
    # R2 = 1 - residual_sum_of_squares / total_sum_of_squares
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return float(1 - (ss_res / ss_tot))

def _zscore_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """
    Normalize a profile using z-score standardization.
    """
    std = np.std(values)
    if std == 0:
        raise ValueError(
            f"{profile_name} cannot be z-score normalized because its standard "
            "deviation is 0."
        )
    return (values - np.mean(values)) / std


def _minmax_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """
    Normalize a profile to the [0, 1] range.
    """
    value_range = np.max(values) - np.min(values)
    if value_range == 0:
        raise ValueError(
            f"{profile_name} cannot be min-max normalized because its range is 0."
        )
    return (values - np.min(values)) / value_range


def calculate_determination_coefficients(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    predictors: int = 5,
) -> tuple[float, float]:
    """Calculate R2 and adjusted R2 for two aligned profiles.

    Parameters
    ----------
    y_true:
        Reference profile.
    y_pred:
        Profile being evaluated.
    predictors:
        Number of independent predictors used in the model. This is ``k`` in
        the adjusted R2 formula. The default is 5, following the paper context.

    Returns
    -------
    tuple[float, float]
        Standard R2 and adjusted R2.

    How to use
    ----------
    Use this function after both profiles have the same length and have been
    normalized as needed for the comparison you want to make.
    """

    if len(y_true) != len(y_pred):
        raise ValueError(
            f"The profiles are not aligned: MATLAB has {len(y_true)} samples "
            f"and Python has {len(y_pred)} samples."
        )

    n = len(y_true)
    if n <= predictors + 1:
        raise ValueError(
            f"There are not enough samples ({n}) to calculate adjusted R2 with "
            f"{predictors} predictors."
        )

    r2 = _r2_score(y_true, y_pred)

    # Adjusted R2 penalizes the score by the number of predictors:
    # R2_corr = 1 - ((1 - R2) * (n - 1)) / (n - k - 1)
    r2_corr = 1 - (((1 - r2) * (n - 1)) / (n - predictors - 1))
    return r2, float(r2_corr)


def main():
    # Read and clean profile
    df_matlab = pd.read_csv(MATLAB_PROFILE, header=None)
    y_true = pd.to_numeric(df_matlab.iloc[:, 0], errors="coerce").dropna().to_numpy(
        dtype=float
    )

    # The generated Excel profile stores the total load in the "Total" column
    # (column H in the current exported file).
    df_python = pd.read_excel(PYTHON_PROFILE)
    total_columns = [
        column for column in df_python.columns if str(column).strip().lower() == "total"
    ]
    if not total_columns:
        raise ValueError(f"The 'Total' column was not found in {PYTHON_PROFILE}")
    y_pred = pd.to_numeric(df_python[total_columns[0]], errors="coerce").dropna().to_numpy(
        dtype=float
    )

    # 1) Annual-energy normalization compares how each profile distributes its
    # yearly total across all 15-minute samples.
    y_true_annual = _normalize_profile(y_true, "Perfil_MATLAB.csv")
    y_pred_annual = _normalize_profile(y_pred, PYTHON_PROFILE.name)
    r2_annual, r2_corr_annual = calculate_determination_coefficients(
        y_true_annual,
        y_pred_annual,
    )

    # 2) Z-score compares relative deviations from each profile's own mean.
    y_true_zscore = _zscore_profile(y_true, "Perfil_MATLAB.csv")
    y_pred_zscore = _zscore_profile(y_pred, PYTHON_PROFILE.name)
    r2_zscore, r2_corr_zscore = calculate_determination_coefficients(
        y_true_zscore,
        y_pred_zscore,
    )

    # 3) Check whether a calendar/time offset improves the temporal match.
    best_r2_zscore, best_r2_corr_zscore, best_shift_zscore = _best_shift_r2(
        y_true_zscore,
        y_pred_zscore,
        max_shift=672,
    )

    # 4) Load-duration curve comparison sorts both profiles from highest to
    # lowest demand. This compares distribution, not timestamp alignment.
    y_true_duration = np.sort(y_true_zscore)[::-1]
    y_pred_duration = np.sort(y_pred_zscore)[::-1]
    r2_duration, r2_corr_duration = calculate_determination_coefficients(
        y_true_duration,
        y_pred_duration,
    )

    # 5) Min-max normalization compares each value's relative position between
    # the profile minimum and maximum.
    y_true_minmax = _minmax_profile(y_true, "Perfil_MATLAB.csv")
    y_pred_minmax = _minmax_profile(y_pred, PYTHON_PROFILE.name)
    r2_minmax, r2_corr_minmax = calculate_determination_coefficients(
        y_true_minmax,
        y_pred_minmax,
    )

    print(f"MATLAB profile: {MATLAB_PROFILE}")
    print(f"Python profile: {PYTHON_PROFILE}")
    print(f"Compared samples: {len(y_true)}")
    print("")
    print("Point-by-point temporal comparison:")
    print(f"R^2 annual-energy normalized: {r2_annual:.4f}")
    print(f"R^2_corr annual-energy normalized: {r2_corr_annual:.4f}")
    print(f"R^2 z-score: {r2_zscore:.4f}")
    print(f"R^2_corr z-score: {r2_corr_zscore:.4f}")
    print(f"R^2 min-max: {r2_minmax:.4f}")
    print(f"R^2_corr min-max: {r2_corr_minmax:.4f}")
    print("")
    print("Best temporal comparison with maximum shift of +/- 1 week:")
    print(f"Shift applied to the Python profile: {best_shift_zscore} samples")
    print(f"Time equivalent: {_shift_to_time(best_shift_zscore)}")
    print(f"R^2 z-score with shift: {best_r2_zscore:.4f}")
    print(f"R^2_corr z-score with shift: {best_r2_corr_zscore:.4f}")
    print("")
    print("Load-duration-curve comparison:")
    print(f"R^2 z-score load-duration curve: {r2_duration:.4f}")
    print(f"R^2_corr z-score load-duration curve: {r2_corr_duration:.4f}")


if __name__ == "__main__":
    main()
