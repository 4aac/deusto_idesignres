import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score


BASE_PATH = Path(__file__).resolve().parents[1]
GENERATED_PROFILE = (
    BASE_PATH
    / "Generated"
    / "load_profiles"
    / "iDesign_RES_Iron and steel_ISI-DE.xlsx"
)
ELMAS_PROFILE = (
    BASE_PATH
    / "Data"
    / "General"
    / "23889780"
    / "ELMAS_dataset"
    / "ELMAS_dataset"
    / "Time_series_18_clusters.csv"
)

SUPPORTED_RESOLUTIONS = {15, 60}


def _normalize_profile(values: np.ndarray, profile_name: str) -> np.ndarray:
    """
    Normalize a profile by its annual total energy.
    """
    total = np.sum(values)
    if total == 0:
        raise ValueError(f"{profile_name} cannot be normalized because its sum is 0.")
    return values / total


def _shift_to_time(shift: int, minutes_per_sample: int) -> str:
    """
    Convert a sample shift into a readable time offset.
    """
    total_minutes = abs(shift) * minutes_per_sample
    hours, minutes = divmod(total_minutes, 60)
    sign = "-" if shift < 0 else "+"
    return f"{sign}{hours} h {minutes} min"


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


def _read_table(path: Path) -> pd.DataFrame:
    """
    Read CSV or Excel input while preserving common generated-profile headers.
    """
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, sep=";", decimal=",")
        if df.shape[1] == 1:
            df = pd.read_csv(path)
        return df

    raise ValueError(f"Unsupported profile file type: {path}")


def _find_column(df: pd.DataFrame, requested_column: str | None, path: Path) -> str:
    """
    Return the requested column, or the first numeric-looking data column.
    """
    if requested_column is not None:
        for column in df.columns:
            if str(column).strip() == str(requested_column).strip():
                return column
        raise ValueError(f"Column '{requested_column}' was not found in {path}")

    for column in df.columns:
        if str(column).strip().lower() in {"time", "application", "unit"}:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        if values.notna().any():
            return column

    raise ValueError(f"No numeric profile column was found in {path}")


def _find_time_column(df: pd.DataFrame) -> str | None:
    """
    Return a likely timestamp column when present.
    """
    for column in df.columns:
        if str(column).strip().lower() in {"time", "application"}:
            return column
    return None


def _parse_timestamps(values: pd.Series) -> pd.Series:
    """
    Parse profile timestamps with the expected project format.
    """
    return pd.to_datetime(
        values,
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )


def load_profile(
    path: Path,
    column: str | None,
    resolution_minutes: int,
    profile_name: str,
) -> pd.Series:
    """
    Load one profile column as a numeric pandas Series.
    """
    path = Path(path)
    if resolution_minutes not in SUPPORTED_RESOLUTIONS:
        raise ValueError(
            f"{profile_name} resolution must be one of {sorted(SUPPORTED_RESOLUTIONS)} minutes."
        )

    df = _read_table(path)
    value_column = _find_column(df, column, path)
    values = pd.to_numeric(df[value_column], errors="coerce")

    time_column = _find_time_column(df)
    if time_column is not None:
        timestamps = _parse_timestamps(df[time_column])
        profile = pd.Series(values.to_numpy(), index=timestamps, name=profile_name)
        profile = profile[profile.index.notna()]
    else:
        profile = pd.Series(values.to_numpy(), name=profile_name)

    profile = profile.dropna().astype(float)
    if profile.empty:
        raise ValueError(f"{profile_name} does not contain valid numeric data.")

    return profile


def convert_resolution(
    profile: pd.Series,
    source_resolution: int,
    target_resolution: int,
    profile_name: str,
) -> pd.Series:
    """
    Convert profile resolution. Power values are averaged when downsampling.
    """
    if target_resolution not in SUPPORTED_RESOLUTIONS:
        raise ValueError(
            f"Target resolution must be one of {sorted(SUPPORTED_RESOLUTIONS)} minutes."
        )
    if source_resolution == target_resolution:
        return profile
    if source_resolution > target_resolution:
        raise ValueError(
            f"{profile_name} is {source_resolution} minutes and cannot be upsampled "
            f"to {target_resolution} minutes."
        )
    if target_resolution % source_resolution != 0:
        raise ValueError(
            f"{profile_name} cannot be converted from {source_resolution} to "
            f"{target_resolution} minutes."
        )

    if isinstance(profile.index, pd.DatetimeIndex):
        return profile.resample(f"{target_resolution}min").mean().dropna()

    factor = target_resolution // source_resolution
    usable_samples = (len(profile) // factor) * factor
    if usable_samples == 0:
        raise ValueError(f"{profile_name} does not have enough samples to downsample.")

    values = profile.iloc[:usable_samples].to_numpy(dtype=float)
    values = values.reshape(-1, factor).mean(axis=1)
    return pd.Series(values, name=profile.name)


def align_profiles(x_profile: pd.Series, y_profile: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Align profiles by timestamp when possible, otherwise by shortest length.
    """
    if isinstance(x_profile.index, pd.DatetimeIndex) and isinstance(
        y_profile.index, pd.DatetimeIndex
    ):
        common_index = x_profile.index.intersection(y_profile.index)
        if common_index.empty:
            raise ValueError("The profiles do not share any timestamps.")
        return x_profile.loc[common_index], y_profile.loc[common_index]

    samples = min(len(x_profile), len(y_profile))
    if samples == 0:
        raise ValueError("The profiles do not contain aligned samples.")
    return x_profile.iloc[:samples], y_profile.iloc[:samples]


def calculate_determination_coefficients(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    predictors: int = 5,
) -> tuple[float, float]:
    """Calculate R2 and adjusted R2 for two aligned profiles."""
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"The profiles are not aligned: X has {len(y_true)} samples "
            f"and Y has {len(y_pred)} samples."
        )

    n = len(y_true)
    if n <= predictors + 1:
        raise ValueError(
            f"There are not enough samples ({n}) to calculate adjusted R2 with "
            f"{predictors} predictors."
        )

    r2 = float(r2_score(y_true, y_pred))
    r2_corr = 1 - (((1 - r2) * (n - 1)) / (n - predictors - 1))
    return r2, float(r2_corr)


def _best_shift_r2(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    max_shift: int,
    predictors: int = 5,
) -> tuple[float, float, int]:
    """
    Find the circular temporal shift that gives the highest R2.
    """
    best_r2 = -float("inf")
    best_r2_corr = -float("inf")
    best_shift = 0

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


def evaluate_profiles(
    x_profile: pd.Series,
    y_profile: pd.Series,
    x_name: str,
    y_name: str,
    resolution_minutes: int,
) -> None:
    """
    Print R2 comparisons for two already aligned profile series.
    """
    y_true = x_profile.to_numpy(dtype=float)
    y_pred = y_profile.to_numpy(dtype=float)

    y_true_annual = _normalize_profile(y_true, x_name)
    y_pred_annual = _normalize_profile(y_pred, y_name)
    r2_annual, r2_corr_annual = calculate_determination_coefficients(
        y_true_annual,
        y_pred_annual,
    )

    y_true_zscore = _zscore_profile(y_true, x_name)
    y_pred_zscore = _zscore_profile(y_pred, y_name)
    r2_zscore, r2_corr_zscore = calculate_determination_coefficients(
        y_true_zscore,
        y_pred_zscore,
    )

    max_temporal_shift = len(y_true_zscore) - 1
    best_r2_zscore, best_r2_corr_zscore, best_shift_zscore = _best_shift_r2(
        y_true_zscore,
        y_pred_zscore,
        max_shift=max_temporal_shift,
    )

    y_true_duration = np.sort(y_true_zscore)[::-1]
    y_pred_duration = np.sort(y_pred_zscore)[::-1]
    r2_duration, r2_corr_duration = calculate_determination_coefficients(
        y_true_duration,
        y_pred_duration,
    )

    print(f"X profile: {x_name}")
    print(f"Y profile: {y_name}")
    print(f"Resolution: {resolution_minutes} minutes")
    print(f"Compared samples: {len(y_true)}")
    print("")
    print("Point-by-point temporal comparison:")
    print(f"R^2 annual-energy normalized: {r2_annual:.4f}")
    print(f"R^2_corr annual-energy normalized: {r2_corr_annual:.4f}")
    print(f"R^2 z-score: {r2_zscore:.4f}")
    print(f"R^2_corr z-score: {r2_corr_zscore:.4f}")
    print("")
    print("Best temporal comparison over all possible shifts:")
    print(f"Shift applied to the Y profile: {best_shift_zscore} samples")
    print(f"Time equivalent: {_shift_to_time(best_shift_zscore, resolution_minutes)}")
    print(f"R^2 z-score with shift: {best_r2_zscore:.4f}")
    print(f"R^2_corr z-score with shift: {best_r2_corr_zscore:.4f}")
    print("")
    print("Load-duration-curve comparison:")
    print(f"R^2 z-score load-duration curve: {r2_duration:.4f}")
    print(f"R^2_corr z-score load-duration curve: {r2_corr_duration:.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate two load profiles at 15-minute or 60-minute resolution."
    )
    parser.add_argument("--x-path", type=Path, default=GENERATED_PROFILE)
    parser.add_argument("--x-column", default="Total")
    parser.add_argument("--x-resolution", type=int, default=15, choices=sorted(SUPPORTED_RESOLUTIONS))
    parser.add_argument("--x-name", default="Generated profile Total")
    parser.add_argument("--y-path", type=Path, default=ELMAS_PROFILE)
    parser.add_argument("--y-column", default="18")
    parser.add_argument("--y-resolution", type=int, default=60, choices=sorted(SUPPORTED_RESOLUTIONS))
    parser.add_argument("--y-name", default="ELMAS Time_series_18_clusters column 18")
    parser.add_argument("--resolution", type=int, default=60, choices=sorted(SUPPORTED_RESOLUTIONS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    x_profile = load_profile(
        args.x_path,
        args.x_column,
        args.x_resolution,
        args.x_name,
    )
    y_profile = load_profile(
        args.y_path,
        args.y_column,
        args.y_resolution,
        args.y_name,
    )

    x_profile = convert_resolution(
        x_profile,
        args.x_resolution,
        args.resolution,
        args.x_name,
    )
    y_profile = convert_resolution(
        y_profile,
        args.y_resolution,
        args.resolution,
        args.y_name,
    )
    x_profile, y_profile = align_profiles(x_profile, y_profile)

    evaluate_profiles(
        x_profile,
        y_profile,
        args.x_name,
        args.y_name,
        args.resolution,
    )


if __name__ == "__main__":
    main()
