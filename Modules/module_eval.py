"""Evaluation utilities for comparing MATLAB and generated load profiles.

This module compares the MATLAB reference profile stored in
``Helpers/regression_load_profiles/Perfil_MATLAB.csv`` with the generated
Python profile stored in
``Generated/load_profiles/iDesign_RES_Iron and steel_ISI-DE.xlsx``.

It can be executed directly from the repository root:

    python Modules/module_eval.py

The comparison reports several R2 variants:
- Point-by-point comparison after annual-energy normalization.
- Point-by-point comparison after z-score normalization.
- Point-by-point comparison after min-max normalization.
- Best z-score comparison after testing temporal shifts up to one week.
- Load-duration-curve comparison, which ignores calendar order and compares
  the annual distribution of load values.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# scikit-learn is preferred when available. A local fallback is kept so the
# script still works in environments where sklearn is not installed.
try:
    from sklearn.metrics import r2_score
except ImportError:  # pragma: no cover - used only when sklearn is unavailable.
    r2_score = None


# Default repository paths used when the script is executed directly.
BASE_PATH = Path(__file__).resolve().parents[1]
MATLAB_PROFILE = BASE_PATH / "Helpers" / "regression_load_profiles" / "Perfil_MATLAB.csv"
PYTHON_PROFILE = (
    BASE_PATH
    / "Generated"
    / "load_profiles"
    / "iDesign_RES_Iron and steel_ISI-DE.xlsx"
)


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


def _clean_profile(values: pd.Series, profile_name: str) -> np.ndarray:
    """Convert a profile column into a clean numeric numpy array.

    Parameters
    ----------
    values:
        Pandas series read from a CSV or Excel column.
    profile_name:
        Human-readable profile name used in error messages.

    Returns
    -------
    numpy.ndarray
        Numeric profile values with non-numeric rows removed.

    How to use
    ----------
    Use this helper after reading a column that may include header/unit rows,
    for example the Excel ``Total`` column where the first metadata row says
    ``in kW``.
    """

    # Unit/header rows become NaN and are removed. This keeps only real data.
    values = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)

    if len(values) == 0:
        raise ValueError(f"{profile_name} does not contain valid numeric data.")

    return values


def _normalize_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """Normalize a profile by its annual total energy.

    Parameters
    ----------
    values:
        Original profile values.
    profile_name:
        Human-readable profile name used in error messages.

    Returns
    -------
    numpy.ndarray
        Values divided by their annual sum.

    How to use
    ----------
    Use this normalization when the profiles have different units or scales but
    you want to compare how annual demand is distributed over time.
    """

    total = np.sum(values)
    if total == 0:
        raise ValueError(f"{profile_name} cannot be normalized because its sum is 0.")
    return values / total


def _zscore_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """Normalize a profile using z-score standardization.

    Parameters
    ----------
    values:
        Original profile values.
    profile_name:
        Human-readable profile name used in error messages.

    Returns
    -------
    numpy.ndarray
        Standardized values with mean 0 and standard deviation 1.

    How to use
    ----------
    Use z-score when the absolute scale is not important and the goal is to
    compare relative deviations from each profile's average behavior.
    """

    std = np.std(values)
    if std == 0:
        raise ValueError(
            f"{profile_name} cannot be z-score normalized because its standard "
            "deviation is 0."
        )
    return (values - np.mean(values)) / std


def _minmax_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """Normalize a profile to the [0, 1] range.

    Parameters
    ----------
    values:
        Original profile values.
    profile_name:
        Human-readable profile name used in error messages.

    Returns
    -------
    numpy.ndarray
        Values scaled between 0 and 1.

    How to use
    ----------
    Use min-max normalization when you want to compare the relative position of
    each point between the minimum and maximum observed demand.
    """

    value_range = np.max(values) - np.min(values)
    if value_range == 0:
        raise ValueError(
            f"{profile_name} cannot be min-max normalized because its range is 0."
        )
    return (values - np.min(values)) / value_range


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


def _shift_to_time(shift: int, minutes_per_sample: int = 15) -> str:
    """Convert a sample shift into a readable time offset.

    Parameters
    ----------
    shift:
        Number of samples shifted. Negative means the Python profile is shifted
        backwards.
    minutes_per_sample:
        Temporal resolution of each sample. The current profiles use 15-minute
        intervals.

    Returns
    -------
    str
        Human-readable offset, for example ``-1 h 15 min``.
    """

    total_minutes = abs(shift) * minutes_per_sample
    hours, minutes = divmod(total_minutes, 60)
    sign = "-" if shift < 0 else "+"
    return f"{sign}{hours} h {minutes} min"


def load_matlab_profile(path: Path = MATLAB_PROFILE) -> np.ndarray:
    """Load the MATLAB reference profile from CSV.

    Parameters
    ----------
    path:
        Path to the MATLAB CSV file. The default points to
        ``Helpers/regression_load_profiles/Perfil_MATLAB.csv``.

    Returns
    -------
    numpy.ndarray
        Clean numeric MATLAB profile.

    How to use
    ----------
    Call ``load_matlab_profile()`` with no arguments to use the default file, or
    pass another ``Path`` to compare a different MATLAB export.
    """

    # The MATLAB export has a single numeric column and no useful header.
    df = pd.read_csv(path, header=None)
    return _clean_profile(df.iloc[:, 0], "Perfil_MATLAB.csv")


def load_python_profile(path: Path = PYTHON_PROFILE) -> np.ndarray:
    """Load the generated Python profile from Excel.

    Parameters
    ----------
    path:
        Path to the generated ``.xlsx`` load profile. The default points to
        ``Generated/load_profiles/iDesign_RES_Iron and steel_ISI-DE.xlsx``.

    Returns
    -------
    numpy.ndarray
        Clean numeric values from the Excel ``Total`` column.

    How to use
    ----------
    Call ``load_python_profile()`` with no arguments to use the default file, or
    pass another generated profile path. The function searches for the ``Total``
    column case-insensitively and ignores surrounding spaces.
    """

    df = pd.read_excel(path)

    # The relevant demand series is the total load, stored in the Excel column
    # named "Total" (column H in the current exported file).
    total_columns = [
        column for column in df.columns if str(column).strip().lower() == "total"
    ]
    if not total_columns:
        raise ValueError(f"The 'Total' column was not found in {path}")
    return _clean_profile(df[total_columns[0]], path.name)


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


def main() -> None:
    """Run all default comparisons and print the results.

    How to use
    ----------
    Execute this file directly:

        python Modules/module_eval.py

    The function loads the default MATLAB and Python profiles, compares them
    using different normalization strategies, searches for the best temporal
    shift, and compares their load-duration curves.
    """

    y_true = load_matlab_profile()
    y_pred = load_python_profile()

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
    print("Excel column used: Total")
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
