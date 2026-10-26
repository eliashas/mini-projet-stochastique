"""Calendar, continuity and tie handling risks of the descriptive analyses."""
import numpy as np
import pandas as pd
import pytest

from sma.diagnostics import evaluate
from sma.heatwaves import analyze_heatwaves, _events


def test_heatwave_calendar_leap_and_threshold_interpolation(tmp_path):
    dates = pd.date_range("2000-01-01", "2002-12-31")
    data = pd.DataFrame({"valid_time": dates, "mean": np.zeros(len(dates))})
    data.loc[data.valid_time.between("2000-02-27", "2000-03-02"), "mean"] = 3.
    result = analyze_heatwaves(data, tmp_path, "synthetic")
    daily = pd.read_csv(tmp_path / "heatwave_daily_thresholds.csv")
    climatology = pd.read_csv(tmp_path / "heatwave_climatology.csv").set_index("month_day")
    assert len(climatology) == 365 and "02-29" not in climatology.index
    feb29 = daily.loc[daily.valid_time == "2000-02-29", "q90_smooth"].item()
    assert feb29 == pytest.approx(.5 * (climatology.loc["02-28", "q90_smooth"] + climatology.loc["03-01", "q90_smooth"]))
    assert climatology.loc["03-01", "day_climatology"] == 60
    events = pd.read_csv(tmp_path / "heatwave_events_min3.csv")
    assert result["events_min3"] == 1
    assert events.duration_days.item() == 5
    assert events.start.item() == "2000-02-27" and events.end.item() == "2000-03-02"


def test_heatwave_gap_breaks_maximal_event():
    data = pd.DataFrame({"valid_time": pd.to_datetime(["2000-01-01", "2000-01-02", "2000-01-04", "2000-01-05"]),
                         "mean": [3., 3., 3., 3.], "q50_smooth": [1., 1., 1., 1.], "q90_smooth": [2., 2., 2., 2.]})
    events = _events(data, 2)
    assert list(events.duration_days) == [2, 2]
    assert _events(data, 3).empty
    assert list(events.intensity_q50_C) == [2., 2.] and list(events.excess_q90_C) == [1., 1.]


def test_diagnostics_midrank_and_event_orientation():
    ensemble = np.array([[0., 0., 2., 2.]])
    for variable in ("max", "min"):
        result = evaluate(ensemble, [0.], 1., variable, years=[2000])
        assert result["per_year"].pit.item() == .25
        assert result["summary"]["brier"] == .25
        assert result["summary"]["event_count"] == (1 if variable == "min" else 0)
        assert result["summary"]["crps"] == .5
    result = evaluate([[0., 2.]], [1.], 1., "max")
    assert result["summary"]["twcrps"] == .25
