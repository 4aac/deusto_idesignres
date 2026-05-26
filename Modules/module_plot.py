import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ========================
#     PLOT SETTINGS
# ========================
PLOT_PREVIEW_STEPS = 672  # First 14 days at 15-minute resolution.
X_TICK_STEP = 96           # One x-axis tick per day.
FIGURE_SIZE = (12, 4)

SHOW_PLOTS_ENV_VAR = "IDESIGN_SHOW_PLOTS"
Y_AXIS_LABEL = "Power in kW"
X_AXIS_LABEL = "Time"
ELECTRIC_Y_SCALE = "linear"
THERMAL_Y_SCALE = "linear"

LEGEND_MAX_COLUMNS = 6
LEGEND_FONT_SIZE = 9


# ========================
#     SERIES SETTINGS
# ========================
ELECTRIC_SUMMED_LABELS = [
    "Lighting",
    "Air compressors",
    "Motor drives",
    "Fans and pumps",
    "Low-enthalpy heat",
    "Others (sum mean)",
]

ELECTRIC_SUMMED_COLORS = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
]

THERMAL_LABELS = [
    "Electricity Other",
    "Electricity Thermal",
    "Non-electric process heat (<100 C)",
    "Non-electric process heat (100-400 C)",
    "Non-electric process heat (400-1000 C)",
    "Non-electric process heat (>1000 C)",
    "Steam (non-electric boilers)",
]

THERMAL_COLORS = [
    "#4E79A7",
    "#59A14F",
    "#F1CE63",
    "#F28E2B",
    "#E15759",
    "#B07AA1",
    "#76B7B2",
]

INVALID_FILENAME_CHARS = ["\\", "/", "*", "?", ":", "[", "]", "|", "<", ">"]


def _flatten_columns(df):
    """Return a copy with simple column names when the input has a MultiIndex."""
    if not isinstance(df.columns, pd.MultiIndex):
        return df

    df = df.copy()
    df.columns = df.columns.get_level_values(0)
    return df


def _safe_name(value):
    """Return a filesystem-safe name fragment."""
    name = str(value)
    for bad_char in INVALID_FILENAME_CHARS:
        name = name.replace(bad_char, " ")
    return "_".join(name.split())


def _auto_colors(n_colors):
    """Return a readable color palette for dynamic column sets."""
    color_map = plt.get_cmap("tab20")
    return [color_map(i / max(n_colors - 1, 1)) for i in range(n_colors)]


def _legend_position(n_labels, force_below=False):
    """Return legend placement settings based on the number of plotted labels."""
    if not force_below and n_labels <= LEGEND_MAX_COLUMNS:
        return {
            "below": False,
            "columns": 1,
            "bottom_margin": None,
        }

    columns = max(1, min(LEGEND_MAX_COLUMNS, n_labels))
    rows = int(np.ceil(n_labels / columns))
    bottom_margin = min(0.58, 0.18 + 0.09 * rows)
    return {
        "below": True,
        "columns": columns,
        "bottom_margin": bottom_margin,
    }


def _select_labels(df, preferred_labels=None):
    """Select preferred labels when all exist, otherwise plot all non-total columns."""
    data_columns = [column for column in df.columns if column != "Total"]
    if preferred_labels and all(label in df.columns for label in preferred_labels):
        return preferred_labels
    return data_columns


def _plot_labels(df, labels):
    """Convert selected columns to the stacked array expected by matplotlib."""
    if not labels:
        raise ValueError("No profile columns found to plot.")
    return np.vstack([df[label].to_numpy() for label in labels])


def _x_axis_labels(index):
    """Return readable x-axis labels for datetime or generic indexes."""
    index = index[:PLOT_PREVIEW_STEPS]
    if isinstance(index, pd.DatetimeIndex):
        return index.strftime("%H:%M %Y-%m-%d").tolist()
    return index.astype(str).tolist()


def _draw_stack_plot(
    df,
    labels,
    colors,
    title,
    y_scale,
    legend_below=False,
):
    """Draw a stacked profile plot and return the matplotlib figure."""
    visible_df = df.iloc[:PLOT_PREVIEW_STEPS]
    x_labels = _x_axis_labels(df.index)
    y_values = _plot_labels(visible_df, labels)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    x_values = np.arange(len(x_labels))
    ax.stackplot(x_values, y_values, labels=labels, colors=colors)

    ax.set_title(title, fontsize=12)
    ax.set_xlabel(X_AXIS_LABEL, fontsize=12)
    ax.set_ylabel(Y_AXIS_LABEL, fontsize=12)
    ax.set_xlim(left=0, right=max(x_values) if len(x_values) else 0)
    ax.set_xticks(x_values[::X_TICK_STEP])
    ax.set_xticklabels(x_labels[::X_TICK_STEP], fontsize=10, rotation=45)
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(True, alpha=0.3)

    if y_scale == "linear":
        y_max = np.nanmax(np.sum(y_values, axis=0)) * 1.05 if y_values.size else 1.0
        ax.set_ylim(bottom=0, top=y_max)
    else:
        ax.set_yscale(y_scale)

    handles, legend_labels = ax.get_legend_handles_labels()
    legend = _legend_position(len(labels), force_below=legend_below)
    if legend["below"]:
        ax.legend(
            list(reversed(handles)),
            list(reversed(legend_labels)),
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=legend["columns"],
            fontsize=LEGEND_FONT_SIZE,
            frameon=False,
        )
        fig.subplots_adjust(bottom=legend["bottom_margin"])
    else:
        ax.legend(
            list(reversed(handles)),
            list(reversed(legend_labels)),
            loc="upper right",
            fontsize=LEGEND_FONT_SIZE,
        )
        fig.tight_layout()

    return fig


def _save_and_finish(fig, output_path):
    """Save the figure and either show or close it depending on environment settings."""
    fig.savefig(output_path, bbox_inches="tight")

    if os.environ.get(SHOW_PLOTS_ENV_VAR, "1") == "0":
        plt.close(fig)
    else:
        plt.show()


def _electrical_title(industry_name, industry_type, country_code, year, weights_mode):
    return f"WZ08 {industry_type} {industry_name} | {country_code} | {int(year)} | {weights_mode}"


def _electrical_file_name(industry_name, industry_type, country_code, year, weights_mode):
    return (
        f"iDesign_RES_{_safe_name(country_code)}_{_safe_name(industry_type)}_"
        f"{_safe_name(industry_name)}_{int(year)}_{_safe_name(weights_mode)}_Diagram.png"
    )


def year_electrical_summed(df, industry_name, industry_type, country_code, year, base_path):
    """Save the annual electrical diagram for the summed six-category profile."""
    df = _flatten_columns(df)
    labels = _select_labels(df, ELECTRIC_SUMMED_LABELS)
    colors = ELECTRIC_SUMMED_COLORS if labels == ELECTRIC_SUMMED_LABELS else _auto_colors(len(labels))
    title = _electrical_title(industry_name, industry_type, country_code, year, "summed")

    fig = _draw_stack_plot(
        df=df,
        labels=labels,
        colors=colors,
        title=title,
        y_scale=ELECTRIC_Y_SCALE,
    )

    file_name = _electrical_file_name(industry_name, industry_type, country_code, year, "summed")
    output_path = Path(base_path) / "Generated" / "diagrams" / file_name
    _save_and_finish(fig, output_path)


def year_electrical_unsummed(df, industry_name, industry_type, country_code, year, base_path):
    """Save the annual electrical diagram with all unsummed end-use columns."""
    df = _flatten_columns(df)
    labels = _select_labels(df)
    colors = _auto_colors(len(labels))
    title = _electrical_title(industry_name, industry_type, country_code, year, "unsummed")

    fig = _draw_stack_plot(
        df=df,
        labels=labels,
        colors=colors,
        title=title,
        y_scale=ELECTRIC_Y_SCALE,
        legend_below=True,
    )

    file_name = _electrical_file_name(industry_name, industry_type, country_code, year, "unsummed")
    output_path = Path(base_path) / "Generated" / "diagrams" / file_name
    _save_and_finish(fig, output_path)


def year_thermal(df, industry_name, industry_type, base_path):
    """Save the annual thermal diagram."""
    df = _flatten_columns(df)
    labels = _select_labels(df, THERMAL_LABELS)
    colors = THERMAL_COLORS if labels == THERMAL_LABELS else _auto_colors(len(labels))
    title = f"{industry_type} {industry_name}"

    fig = _draw_stack_plot(
        df=df,
        labels=labels,
        colors=colors,
        title=title,
        y_scale=THERMAL_Y_SCALE,
        legend_below=len(labels) > LEGEND_MAX_COLUMNS,
    )

    output_path = Path(base_path) / "Generated" / "diagrams" / f"iDesign_RES_{industry_name}_{industry_type}_Diagram.png"
    _save_and_finish(fig, output_path)
