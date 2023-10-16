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

    # NOTE: not "missing 'arg2'", even though we pass arg2 positionally,
    # because we report more accurately than the standard error
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


@pytest.mark.parametrize(
    "a, expected",
    [
        [(1, 2), (1, (2,))],
        [(1,), (1, ())],
    ],
)
def test_cold_call_passes_variadic_posargs(a, expected):
    def testfunc(arg1, *args):
        return arg1, args

    assert cold_call(testfunc, *a) == expected


@pytest.mark.parametrize(
    "kw, expected",
    [
        [{"arg1": "foo", "arg2": "bar"}, ("foo", {"arg2": "bar"})],
        [{"arg1": "foo"}, ("foo", {})],
    ],
)
def test_cold_call_passes_variadic_kwargs(kw, expected):
    def testfunc(*, arg1, **kwargs):
        return arg1, kwargs

    assert cold_call(testfunc, **kw) == expected


_default = object()


@pytest.mark.parametrize(
    "a, kw, expected",
    [
        [(), {}, (_default, _default)],
        [(5,), {}, (5, _default)],
        [(4, 5), {}, (4, 5)],
        [(), {"arg1": 5}, (5, _default)],
        [(), {"arg2": 5}, (_default, 5)],
        [(), {"arg1": 5, "arg2": 5}, (5, 5)],
    ],
)
def test_cold_call_applies_defaults(a, kw, expected):
    def testfunc(arg1=_default, arg2=_default):
        return arg1, arg2

    assert cold_call(testfunc, *a, **kw) == expected
