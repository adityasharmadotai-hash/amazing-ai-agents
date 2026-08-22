"""Expanded employee-language recall (agent/config.py)."""
from __future__ import annotations

from agent import config

NEW_PHRASES = [
    '"my time at * has come to an end"',
    '"affected by the workforce reduction"',
    '"leaving * earlier than expected"',
    '"impacted along with many talented colleagues"',
]


def test_new_phrases_in_employee_group():
    employee = config.QUERY_DICTIONARY["employee"]
    for phrase in NEW_PHRASES:
        assert phrase in employee, f"{phrase!r} not in employee query group"


def test_new_phrases_flow_into_default_queries():
    for phrase in NEW_PHRASES:
        assert phrase in config._DEFAULT_QUERIES


def test_default_query_set_has_no_duplicates():
    assert len(config._DEFAULT_QUERIES) == len(set(config._DEFAULT_QUERIES))
