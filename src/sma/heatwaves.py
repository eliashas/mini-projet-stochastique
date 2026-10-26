"""Descriptive heat waves, on the calendar dates of the supplied phase only."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _save(fig, directory: Path, name: str) -> list[str]:
    paths = []
    for suffix in ("png", "svg"):
        target = directory / f"{name}.{suffix}"
        fig.savefig(target, dpi=160, bbox_inches="tight")
        paths.append(str(target))
    plt.close(fig)
    return paths


def _events(data: pd.DataFrame, minimum_days: int) -> pd.DataFrame:
    """Extract maximal runs, without joining days across missing dates."""
    columns = ["start", "end", "duration_days", "intensity_q50_C",
               "excess_q90_C", "start_year", "max_mean_C"]
    hot = data["mean"].to_numpy() > data["q90_smooth"].to_numpy()
    dates = data["valid_time"].to_numpy()
    records = []
    begin = None
    for i in range(len(data) + 1):
        current_hot = i < len(data) and hot[i]
        continuous = i == 0 or i == len(data) or dates[i] - dates[i - 1] == np.timedelta64(1, "D")
        if begin is not None and (not current_hot or not continuous):
            subset = data.iloc[begin:i]
            if len(subset) >= minimum_days:
                records.append({
                    "start": subset.valid_time.iloc[0].date().isoformat(),
                    "end": subset.valid_time.iloc[-1].date().isoformat(),
                    "duration_days": len(subset),
                    "intensity_q50_C": float((subset["mean"] - subset.q50_smooth).mean()),
                    "excess_q90_C": float((subset["mean"] - subset.q90_smooth).mean()),
                    "start_year": int(subset.valid_time.iloc[0].year),
                    "max_mean_C": float(subset["mean"].max()),
                })
            begin = None
        if current_hot and begin is None:
            begin = i
    return pd.DataFrame.from_records(records, columns=columns)


def analyze_heatwaves(daily: pd.DataFrame, out_dir: Path, phase: str) -> dict:
    """Export q10/q50/q90, circular smoothing, and maximal 3/2-day events.

    The caller controls the admissible period. February 29 is excluded from
    climatology and interpolated only for event detection. The reference is
    descriptive: all supplied years enter the thresholds.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = daily[["valid_time", "mean"]].copy()
    data["valid_time"] = pd.to_datetime(data["valid_time"], errors="raise").dt.normalize()
    data["mean"] = pd.to_numeric(data["mean"], errors="raise")
    data = data.sort_values("valid_time").reset_index(drop=True)
    if len(data) == 0 or data.valid_time.duplicated().any() or not np.isfinite(data["mean"]).all():
        raise ValueError("Heat-wave data must be nonempty, finite, with unique dates.")
    data["month_day"] = data.valid_time.dt.strftime("%m-%d")
    calendar_dates = pd.date_range("2001-01-01", "2001-12-31")
    calendar = calendar_dates.strftime("%m-%d")
    climatology = (data.loc[data.month_day != "02-29"]
                   .groupby("month_day")["mean"].quantile([.1, .5, .9])
                   .unstack().reindex(calendar))
    if climatology.isna().any().any():
        raise ValueError("All 365 calendar dates are required to estimate climatology.")
    climatology.columns = ["q10", "q50", "q90"]
    climatology.index.name = "month_day"
    climatology["day_climatology"] = np.arange(1, 366)
    for label in ("q10", "q50", "q90"):
        # Window [-15,+15], including a circular connection December/January.
        smooth = np.convolve(np.pad(climatology[label].to_numpy(), (15, 15), mode="wrap"),
                             np.ones(31) / 31, mode="valid")
        climatology[f"{label}_smooth"] = smooth
        lookup = climatology[f"{label}_smooth"].to_dict()
        lookup["02-29"] = .5 * (lookup["02-28"] + lookup["03-01"])
        data[f"{label}_smooth"] = data.month_day.map(lookup)
    primary, sensitivity = _events(data, 3), _events(data, 2)
    climatology.to_csv(out_dir / "heatwave_climatology.csv", index=True)
    data.to_csv(out_dir / "heatwave_daily_thresholds.csv", index=False)
    primary.to_csv(out_dir / "heatwave_events_min3.csv", index=False)
    sensitivity.to_csv(out_dir / "heatwave_events_min2.csv", index=False)
    years = np.arange(data.valid_time.dt.year.min(), data.valid_time.dt.year.max() + 1)
    annual = pd.DataFrame({"year": years})
    for minimum_days, events in ((3, primary), (2, sensitivity)):
        count = events.groupby("start_year").size()
        days = events.groupby("start_year")["duration_days"].sum()
        annual[f"events_min{minimum_days}"] = annual.year.map(count).fillna(0).astype(int)
        annual[f"days_min{minimum_days}"] = annual.year.map(days).fillna(0).astype(int)
    annual.to_csv(out_dir / "heatwave_counts_year.csv", index=False)
    figures = []
    fig, ax = plt.subplots(figsize=(10, 4))
    for label, color in (("q10", "#4477aa"), ("q50", "#222222"), ("q90", "#cc6677")):
        ax.plot(calendar_dates, climatology[f"{label}_smooth"], label=label + " lissé", color=color)
    ax.set(xlabel="Jour calendaire (365 jours)", ylabel="Température moyenne journalière (°C)",
           title=f"Brest : cycle saisonnier, référence {years[0]}–{years[-1]}")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m"))
    ax.set_xlim(calendar_dates[0], calendar_dates[-1])
    ax.grid(alpha=.2); ax.legend()
    figures += _save(fig, out_dir, "heatwave_seasonal_cycle")
    fig, ax = plt.subplots(figsize=(8, 5))
    if len(primary):
        scatter = ax.scatter(primary.duration_days, primary.intensity_q50_C, c=primary.start_year,
                             cmap="viridis", alpha=.8, edgecolor="white", linewidth=.3)
        fig.colorbar(scatter, ax=ax, label="Année de début")
    else:
        ax.text(.5, .5, "Aucun événement d'au moins 3 jours", transform=ax.transAxes, ha="center")
    ax.set(xlabel="Durée (jours consécutifs)", ylabel="Anomalie moyenne à q50 lissé (°C)",
           title="Vagues de chaleur : seuil q90 lissé, durée minimale 3 jours")
    ax.grid(alpha=.2)
    figures += _save(fig, out_dir, "heatwave_duration_intensity")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(annual.year, annual.events_min3, label="Durée ≥ 3 jours")
    ax.plot(annual.year, annual.events_min2, label="Sensibilité : durée ≥ 2 jours", alpha=.65)
    ax.set(xlabel="Année de début", ylabel="Nombre d'événements", title="Comptage descriptif des vagues de chaleur")
    ax.legend(); ax.grid(alpha=.2)
    figures += _save(fig, out_dir, "heatwave_counts")
    summary = {
        "phase": phase, "reference_start": data.valid_time.iloc[0].date().isoformat(),
        "reference_end": data.valid_time.iloc[-1].date().isoformat(), "daily_rows": len(data),
        "missing_dates": int((data.valid_time.iloc[-1] - data.valid_time.iloc[0]).days + 1 - len(data)),
        "feb29_days": int((data.month_day == "02-29").sum()), "climatology_days": 365,
        "smoothing_window_days": 31, "events_min3": len(primary), "events_min2": len(sensitivity),
        "maximum_duration_min3_days": int(primary.duration_days.max()) if len(primary) else 0,
        "mean_intensity_min3_C": float(primary.intensity_q50_C.mean()) if len(primary) else None,
        "mean_excess_q90_min3_C": float(primary.excess_q90_C.mean()) if len(primary) else None,
        "units": "°C; duration in days", "event_definition": "maximal consecutive runs mean > smoothed q90",
        "intensity_definition": "event mean(mean temperature - smoothed q50)",
        "excess_definition": "event mean(mean temperature - smoothed q90)",
        "feb29_rule": "excluded from quantiles; thresholds interpolate February 28 / March 1",
        "interpretation": "descriptive climatology over supplied reference period; not out-of-sample prediction",
        "figures": figures,
    }
    (out_dir / "heatwave_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary
