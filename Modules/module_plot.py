from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ELECTRIC_LABELS = [
    "Space heating",
    "Hot water",
    "Process heat",
    "Space cooling",
    "Process cooling",
    "Lighting",
    "ICT",
    "Mechanical drives",
]

ELECTRIC_COLORS = [
    (254 / 255, 188 / 255, 195 / 255),  # light pink
    (255 / 255, 89 / 255, 105 / 255),   # pink-red
    (172 / 255, 0 / 255, 16 / 255),     # dark red
    (82 / 255, 203 / 255, 190 / 255),   # turquoise
    (49 / 255, 164 / 255, 151 / 255),   # teal
    (254 / 255, 198 / 255, 48 / 255),   # yellow
    (146 / 255, 208 / 255, 80 / 255),   # light green
    (93 / 255, 115 / 255, 115 / 255),   # gray
]

THERMAL_LABELS = [
    "Space heating",
    "Hot water",
    "< 100 �C",
    "100 �C - 500 �C",
    "500 �C - 1000 �C",
    ">1000 �C",
]

THERMAL_COLORS = [
    (200 / 255, 200 / 255, 200 / 255),  # light gray
    (93 / 255, 115 / 255, 115 / 255),   # dark gray
    (255 / 255, 201 / 255, 206 / 255),  # light pink
    (255 / 255, 117 / 255, 130 / 255),  # pink
    (255 / 255, 1 / 255, 25 / 255),     # red
    (150 / 255, 0 / 255, 14 / 255),     # dark red
]



def _flatten_columns(df):
    """
    Flatten MultiIndex columns to the first level for consistent plotting.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def _require_columns(df, labels):
    """
    Ensure required labels exist in the DataFrame before plotting.
    """
    missing = [label for label in labels if label not in df.columns]
    if missing:
        raise KeyError(
            "Missing columns for plotting: "
            + ", ".join(missing)
            + ". Available columns: "
            + ", ".join(map(str, df.columns))
        )


def _build_stack(df, labels):
    """
    Build a stacked array for stackplot from ordered labels.
    """
    return np.vstack([df[label].to_numpy() for label in labels])


def _format_time_labels(index, limit=None):
    """
    Format index values for x-axis labels, limiting to a subset if needed.
    """
    if limit is not None:
        index = index[:limit]
    if isinstance(index, pd.DatetimeIndex):
        return index.strftime("%H:%M %Y-%m-%d").tolist()
    return index.astype(str).tolist()


def _plot_stack(x_labels, y_stack, labels, colors, xtick, title=None, y_max=None):
    """
    Render a stacked area plot with consistent styling and axes.
    """
    x = np.arange(len(x_labels))
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.stackplot(x, y_stack, labels=labels, colors=colors)

    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Power in kW", fontsize=12)

    ax.set_xticks(x[::xtick])
    ax.set_xticklabels(x_labels[::xtick], fontsize=10, rotation=45)
    ax.tick_params(axis="y", labelsize=10)

    if title:
        ax.set_title(title, fontsize=12)

    ax.legend(reversed(ax.get_legend_handles_labels()[0]), reversed(labels), loc="upper right", fontsize=9)
    ax.set_xlim(left=0, right=max(x) if len(x) else 0)

    if y_max is None and y_stack.size:
        y_max = np.nanmax(np.sum(y_stack, axis=0)) * 1.05
    if y_max:
        ax.set_ylim(bottom=0, top=y_max)

    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    return fig



def day_electrical(df):
    """
    Plot a single-day electrical profile (96 time steps).
    """
    df = _flatten_columns(df)
    _require_columns(df, ELECTRIC_LABELS)

    x_labels = pd.date_range(start="2020-01-01", periods=96, freq="15min").strftime("%H:%M").tolist()
    y_stack = _build_stack(df, ELECTRIC_LABELS)

    _plot_stack(x_labels, y_stack, ELECTRIC_LABELS, ELECTRIC_COLORS, xtick=8)
    plt.show()


def year_electrical(df, industry_name, industry_type, base_path):
    """
    Plot and save a two-week electrical profile overview.
    """
    df = _flatten_columns(df)
    _require_columns(df, ELECTRIC_LABELS)

    x_labels = _format_time_labels(df.index, limit=1344)
    y_stack = _build_stack(df.iloc[:1344], ELECTRIC_LABELS)

    fig = _plot_stack(
        x_labels,
        y_stack,
        ELECTRIC_LABELS,
        ELECTRIC_COLORS,
        xtick=96,
        title=f"WZ08 {industry_type} {industry_name}",
    )

    base_path = Path(base_path)
    output_path = base_path / "Electrical" / "Diagrams" / f"{industry_name}_Diagram.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()


def day_thermal(df):
    """
    Plot a single-day thermal profile (96 time steps).
    """
    df = _flatten_columns(df)
    _require_columns(df, THERMAL_LABELS)

    x_labels = pd.date_range(start="2020-01-01", periods=96, freq="15min").strftime("%H:%M").tolist()
    y_stack = _build_stack(df, THERMAL_LABELS)

    _plot_stack(x_labels, y_stack, THERMAL_LABELS, THERMAL_COLORS, xtick=8)
    plt.show()


def year_thermal(df, industry_name, industry_type, base_path):
    """
    Plot and save a two-week thermal profile overview.
    """
    df = _flatten_columns(df)
    _require_columns(df, THERMAL_LABELS)

    x_labels = _format_time_labels(df.index, limit=1344)
    y_stack = _build_stack(df.iloc[:1344], THERMAL_LABELS)

    fig = _plot_stack(
        x_labels,
        y_stack,
        THERMAL_LABELS,
        THERMAL_COLORS,
        xtick=96,
        title=f"WZ08 {industry_type} {industry_name}",
    )

    base_path = Path(base_path)
    output_path = base_path / "Thermal" / "Diagrams" / f"{industry_name}_Diagram.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()
