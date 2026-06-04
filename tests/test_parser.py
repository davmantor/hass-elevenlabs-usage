"""Tests for the ElevenLabs analytics parser."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import only the pure functions — avoids needing a running HA instance.
from custom_components.hass_elevenlabs_usage import _parse_analytics, _build_data  # noqa: E402


def test_parse_credits_and_calls():
    raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_types": ["DateTime", "Float", "Int"],
        "column_units": ["ms", "credits", None],
        "rows": [
            [1748908800000, 0.5, 3],
            [1748995200000, 0.25, 2],
        ],
    }
    credits, calls = _parse_analytics(raw)
    assert credits == 0.75
    assert calls == 5


def test_parse_empty_rows_returns_none():
    raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_types": ["DateTime", "Float", "Int"],
        "column_units": ["ms", "credits", None],
        "rows": [],
    }
    credits, calls = _parse_analytics(raw)
    assert credits is None
    assert calls is None


def test_parse_missing_credits_column():
    raw = {
        "columns": ["timestamp", "request_count"],
        "column_types": ["DateTime", "Int"],
        "column_units": ["ms", None],
        "rows": [[1748908800000, 5]],
    }
    credits, calls = _parse_analytics(raw)
    assert credits is None
    assert calls == 5


def test_parse_missing_calls_column():
    raw = {
        "columns": ["timestamp", "credits"],
        "column_types": ["DateTime", "Float"],
        "column_units": ["ms", "credits"],
        "rows": [[1748908800000, 1.5]],
    }
    credits, calls = _parse_analytics(raw)
    assert credits == 1.5
    assert calls is None


def test_parse_single_row():
    raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_units": ["ms", "credits", None],
        "rows": [[1748908800000, 0.123456, 1]],
    }
    credits, calls = _parse_analytics(raw)
    assert credits == 0.123456
    assert calls == 1


def test_build_data_maps_all_fields():
    subscription = {"subscription": {"tier": "creator"}}
    today_raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_units": ["ms", "credits", None],
        "rows": [[1748908800000, 0.5, 3]],
    }
    week_raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_units": ["ms", "credits", None],
        "rows": [[1748908800000, 2.0, 10]],
    }
    month_raw = {
        "columns": ["timestamp", "credits", "request_count"],
        "column_units": ["ms", "credits", None],
        "rows": [[1748908800000, 5.0, 25]],
    }
    data = _build_data(subscription, today_raw, week_raw, month_raw)
    assert data["subscription_tier"] == "creator"
    assert data["credits_used_today"] == 0.5
    assert data["calls_today"] == 3
    assert data["credits_used_week"] == 2.0
    assert data["calls_week"] == 10
    assert data["credits_used_month"] == 5.0


def test_build_data_handles_missing_tier():
    subscription = {}
    empty = {"columns": [], "column_units": [], "rows": []}
    data = _build_data(subscription, empty, empty, empty)
    assert "subscription_tier" not in data
    assert data["credits_used_today"] is None
    assert data["calls_today"] is None
