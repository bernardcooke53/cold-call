from __future__ import annotations

from dataclasses import dataclass

import pytest

from cold_call import ColdCaller


@dataclass
class State(ColdCaller):
    param1: str
    param2: int


@pytest.mark.parametrize(
    "param1, param2, fn, expected",
    [
        ("foo", 3, (lambda param1: param1.upper()), "FOO"),
        ("foo", 3, (lambda param1, param2: param1 * param2), "foofoofoo"),
    ],
)
def test_cold_caller(param1, param2, fn, expected):
    state = State(param1=param1, param2=param2)
    assert state.call(fn) == expected


@pytest.mark.parametrize(
    "param1, param2, fn, expected",
    [
        ("foo", 3, (lambda param1: param1.upper()), "BAR"),
        # positional arguments don't override
        ("foo", 3, (lambda param1, param2: param1 * param2), "bar"),
    ],
)
def test_cold_caller_with_posarg_overrides(param1, param2, fn, expected):
    state = State(param1="bar", param2=1)
    assert state.call(fn, param1, param2) == expected


@pytest.mark.parametrize(
    "param1, param2, fn, expected",
    [
        ("foo", 3, (lambda param1: param1.upper()), "FOO"),
        ("foo", 3, (lambda param1, param2: param1 * param2), "foofoofoo"),
    ],
)
def test_cold_caller_with_kwarg_overrides(param1, param2, fn, expected):
    state = State(param1="bar", param2=1)
    assert state.call(fn, param1=param1, param2=param2) == expected


def test_cold_caller_with_additional_posonly_arg():
    def testfunc(param0, /, param2):
        return param0 * param2

    state = State(param1="foo", param2=2)
    assert state.call(testfunc, "bar") == "barbar"


def test_cold_caller_with_additional_arg():
    def testfunc(param1, param3):
        return param1 * param3

    state = State(param1="foo", param2=2)

    assert state.call(testfunc, param3=4) == "foofoofoofoo"
