from __future__ import annotations

import functools

import pytest

from cold_call import cold_callable


@pytest.fixture
def testfunc():
    def test_func(arg: int) -> str:
        del arg
        return "the result"

    return test_func


@pytest.fixture
def cold_callable_testfunc(testfunc):
    return cold_callable(testfunc)


def test_cold_callable_works(testfunc, cold_callable_testfunc):
    for attr in functools.WRAPPER_ASSIGNMENTS:
        assert getattr(testfunc, attr) == getattr(
            cold_callable_testfunc, attr
        ), f"{attr} is different"

    assert cold_callable_testfunc(arg=5, foo="bar") == "the result"
