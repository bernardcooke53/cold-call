from __future__ import annotations

import pytest

from cold_call import cold_call


@pytest.mark.parametrize(
    "a, kw, expected",
    [
        ((), {"arg1": "foo", "arg2": 3}, ("foo", 3)),
        (("foo",), {"arg2": 3}, ("foo", 3)),
        (("foo", 3), {}, ("foo", 3)),
        # keyword-arg value takes precedence
        (
            ("bar",),
            {"arg1": "foo", "arg2": 3},
            ("foo", 3),
        ),
    ],
)
def test_cold_call_basic_signature(a, kw, expected):
    def testfunc(arg1: str, arg2: int) -> tuple[str, int]:
        return arg1, arg2

    assert cold_call(testfunc, *a, **kw) == expected


@pytest.mark.parametrize(
    "a, kw, error_cls, match",
    [
        (
            (),
            {"arg1": "foo"},
            TypeError,
            "missing 1 required positional argument: 'arg2'",
        ),
    ],
)
def test_cold_call_fails_basic_signature(a, kw, error_cls, match):
    def testfunc(arg1: str, arg2: int) -> tuple[str, int]:
        return arg1, arg2

    with pytest.raises(error_cls, match=match):
        cold_call(testfunc, *a, **kw)


def test_cold_call_fails_keyword_only_args():
    def testfunc(arg1: str, *, arg2: int) -> None:
        pass

    with pytest.raises(
        TypeError, match="missing 1 required keyword-only argument: 'arg2'"
    ):
        cold_call(testfunc, 1, 2)


def test_cold_call_fails_not_enough_positional_arguments():
    def testfunc(arg1: str, /, arg2: str) -> None:
        pass

    with pytest.raises(
        TypeError, match="missing 1 required positional argument: 'arg1'"
    ):
        cold_call(testfunc, arg2="abc")


def test_cold_call_identifies_posonly_args_from_kwargs():
    def testfunc(
        arg1,
        arg2,
        /,
    ):
        return arg1 + arg2

    assert cold_call(testfunc, arg1=1, arg2=2, arg3=3) == 3
