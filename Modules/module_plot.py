# -*- coding: utf-8 -*-
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ELECTRIC_SUMMED_LABELS = [
    "Lighting",
    "Air compressors",
    "Motor drives",
    "Fans and pumps",
    "Low-enthalpy heat",
    "Others (sum mean)",
]

ELECTRIC_COLORS = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
]

THERMAL_LABELS = [
    "Space heating",
    "Hot water",
    "< 100 Â°C",
    "100 Â°C - 500 Â°C",
    "500 Â°C - 1000 Â°C",
    ">1000 Â°C",
]

THERMAL_COLORS = [
    (200 / 255, 200 / 255, 200 / 255),
    (93 / 255, 115 / 255, 115 / 255),
    (255 / 255, 201 / 255, 206 / 255),
    (255 / 255, 117 / 255, 130 / 255),
    (255 / 255, 1 / 255, 25 / 255),
    (150 / 255, 0 / 255, 14 / 255),
]

ELECTRIC_Y_SCALE = "linear"
THERMAL_Y_SCALE = "linear"


def _safe_name(value):
    name = str(value)
    for bad_char in ["\\", "/", "*", "?", ":", "[", "]", "|", "<", ">"]:
        name = name.replace(bad_char, " ")
    return "_".join(name.split())


def _flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def _time_labels(index, limit=None):
    if limit is not None:
        index = index[:limit]
    if isinstance(index, pd.DatetimeIndex):
        return index.strftime("%H:%M %Y-%m-%d").tolist()
    return index.astype(str).tolist()


def _stack(df, labels):
    return np.vstack([df[label].to_numpy() for label in labels])


def _auto_colors(n):
    cmap = plt.get_cmap("tab20")
    return [cmap(i / max(n - 1, 1)) for i in range(n)]


def _legend_layout(n_labels):
    ncol = max(1, min(6, n_labels))
    nrows = int(np.ceil(n_labels / ncol))
    bottom = min(0.58, 0.18 + 0.09 * nrows)
    return ncol, bottom


def _plot_stack(
    x_labels,
    y_stack,
    labels,
    colors,
    xtick,
    title=None,
    y_scale="linear",
    legend_below=False,
    legend_ncol=3,
    legend_bottom=0.2,
):
    fig, ax = plt.subplots(figsize=(12, 4))
    x = np.arange(len(x_labels))
    ax.stackplot(x, y_stack, labels=labels, colors=colors)

    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Power in kW", fontsize=12)
    ax.set_xlim(left=0, right=max(x) if len(x) else 0)
    ax.set_xticks(x[:: max(1, xtick)])
    ax.set_xticklabels(x_labels[:: max(1, xtick)], fontsize=10, rotation=45)
    ax.tick_params(axis="y", labelsize=10)
    ax.grid(True, alpha=0.3)

    if title:
        ax.set_title(title, fontsize=12)

    y_max = np.nanmax(np.sum(y_stack, axis=0)) * 1.05 if y_stack.size else 1.0
    if y_scale != "linear":
        ax.set_yscale(y_scale)
    else:
        ax.set_ylim(bottom=0, top=y_max)

    handles, legend_labels = ax.get_legend_handles_labels()
    if legend_below:
        ax.legend(
            list(reversed(handles)),
            list(reversed(legend_labels)),
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            ncol=legend_ncol,
            fontsize=9,
            frameon=False,
        )
        fig.subplots_adjust(bottom=legend_bottom)
    else:
        ax.legend(
            list(reversed(handles)),
            list(reversed(legend_labels)),
            loc="upper right",
            fontsize=9,
        )
        fig.tight_layout()

    return fig


def day_electrical_summed(df):
    df = _flatten_columns(df)
    labels = ELECTRIC_SUMMED_LABELS
    x_labels = pd.date_range(start="2020-01-01", periods=96, freq="15min").strftime("%H:%M").tolist()
    y_stack = _stack(df, labels)
    _plot_stack(x_labels, y_stack, labels, ELECTRIC_COLORS, xtick=8, y_scale=ELECTRIC_Y_SCALE)
    plt.show()


def day_electrical_unsummed(df):
    df = _flatten_columns(df)
    labels = [c for c in df.columns if c != "Total"]
    x_labels = pd.date_range(start="2020-01-01", periods=96, freq="15min").strftime("%H:%M").tolist()
    y_stack = _stack(df, labels)
    colors = _auto_colors(len(labels))
    legend_ncol, legend_bottom = _legend_layout(len(labels))
    _plot_stack(
        x_labels,
        y_stack,
        labels,
        colors,
        xtick=8,
        y_scale=ELECTRIC_Y_SCALE,
        legend_below=True,
        legend_ncol=legend_ncol,
        legend_bottom=legend_bottom,
    )
    plt.show()


def year_electrical_summed(df, industry_name, industry_type, base_path):
    df = _flatten_columns(df)
    labels = ELECTRIC_SUMMED_LABELS
    x_labels = _time_labels(df.index, limit=1344)
    y_stack = _stack(df.iloc[:1344], labels)
    fig = _plot_stack(
        x_labels,
        y_stack,
        labels,
        ELECTRIC_COLORS,
        xtick=96,
        title=f"WZ08 {industry_type} {industry_name}",
        y_scale=ELECTRIC_Y_SCALE,
    )
    output_path = Path(base_path) / "Generated" / "diagrams" / f"{industry_name}_Diagram.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()


def year_electrical_unsummed(df, industry_name, industry_type, country_code, year, base_path):
    df = _flatten_columns(df)
    labels = [c for c in df.columns if c != "Total"]
    x_labels = _time_labels(df.index, limit=1344)
    y_stack = _stack(df.iloc[:1344], labels)
    colors = _auto_colors(len(labels))
    legend_ncol, legend_bottom = _legend_layout(len(labels))

    fig = _plot_stack(
        x_labels,
        y_stack,
        labels,
        colors,
        xtick=96,
        title=f"WZ08 {industry_type} {industry_name} | {country_code} | {year} | unsummed (rerun)",
        y_scale=ELECTRIC_Y_SCALE,
        legend_below=True,
        legend_ncol=legend_ncol,
        legend_bottom=legend_bottom,
    )

    file_name = (
        f"iDesign_RES_{_safe_name(country_code)}_{_safe_name(industry_type)}_"
        f"{_safe_name(industry_name)}_{int(year)}_unsummed_rerun_Diagram.png"
    )
    output_path = Path(base_path) / "Generated" / "diagrams" / file_name
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()


def year_electrical(df, industry_name, industry_type, base_path):
    year_electrical_summed(df, industry_name, industry_type, base_path)


def day_electrical(df):
    day_electrical_summed(df)


def day_thermal(df):
    df = _flatten_columns(df)
    labels = THERMAL_LABELS
    x_labels = pd.date_range(start="2020-01-01", periods=96, freq="15min").strftime("%H:%M").tolist()
    y_stack = _stack(df, labels)
    _plot_stack(x_labels, y_stack, labels, THERMAL_COLORS, xtick=8, y_scale=THERMAL_Y_SCALE)
    plt.show()


def year_thermal(df, industry_name, industry_type, base_path):
    df = _flatten_columns(df)
    labels = THERMAL_LABELS
    x_labels = _time_labels(df.index, limit=1344)
    y_stack = _stack(df.iloc[:1344], labels)
    fig = _plot_stack(
        x_labels,
        y_stack,
        labels,
        THERMAL_COLORS,
        xtick=96,
        title=f"WZ08 {industry_type} {industry_name}",
        y_scale=THERMAL_Y_SCALE,
    )
    output_path = Path(base_path) / "Generated" / "diagrams" / f"iDesign_RES_{industry_name}_{industry_type}_Diagram.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()
