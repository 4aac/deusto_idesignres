import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_PATH = Path(__file__).resolve().parents[1]
MATLAB_PROFILE = BASE_PATH / "Helpers" / "regression_load_profiles" / "Perfil_MATLAB.csv"
OUTPUT_PATH = BASE_PATH / "Generated" / "matlab_diagrams" / "Perfil_MATLAB_Diagram.png"

PLOT_PREVIEW_STEPS = 672  # First week at 15-minute resolution.
X_TICK_STEP = 96  # One x-axis tick per day.
FIGURE_SIZE = (12, 4)

SHOW_PLOTS_ENV_VAR = "IDESIGN_SHOW_PLOTS"
Y_AXIS_LABEL = "Power in kW"
X_AXIS_LABEL = "Time"
PROFILE_LABEL = "Perfil_MATLAB"


def _save_and_finish(fig, output_path):
    """Save the figure and either show or close it depending on environment settings."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")

    if os.environ.get(SHOW_PLOTS_ENV_VAR, "1") == "0":
        plt.close(fig)
    else:
        plt.show()


def plot_matlab_profile():
    """Plot the MATLAB reference profile using the same preview style as module_plot."""
    df_matlab = pd.read_csv(MATLAB_PROFILE, header=None, names=[PROFILE_LABEL])
    profile = pd.to_numeric(df_matlab[PROFILE_LABEL], errors="coerce").dropna()
    visible_profile = profile.iloc[:PLOT_PREVIEW_STEPS]

    x_values = np.arange(len(visible_profile))
    x_labels = visible_profile.index.astype(str).tolist()

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.stackplot(
        x_values,
        visible_profile.to_numpy(dtype=float),
        labels=[PROFILE_LABEL],
        colors=["#0072B2"],
    )

    ax.set_title(PROFILE_LABEL, fontsize=12)
    ax.set_xlabel(X_AXIS_LABEL, fontsize=12)
    ax.set_ylabel(Y_AXIS_LABEL, fontsize=12)
    ax.set_xlim(left=0, right=max(x_values) if len(x_values) else 0)
    ax.set_xticks(x_values[::X_TICK_STEP])
    ax.set_xticklabels(x_labels[::X_TICK_STEP], fontsize=10, rotation=45)
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(True, alpha=0.3)

    y_max = np.nanmax(visible_profile.to_numpy(dtype=float)) * 1.05
    ax.set_ylim(bottom=0, top=y_max)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()

    _save_and_finish(fig, OUTPUT_PATH)


if __name__ == "__main__":
    plot_matlab_profile()
