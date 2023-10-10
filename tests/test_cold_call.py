from __future__ import annotations

import pytest

from cold_call import cold_call


@pytest.mark.parametrize(
    "dct, a, kw, expected",
    [
        ({"arg1": "foo", "arg2": 3}, (), {}, ("foo", 3)),
        ({"arg2": 3}, ("foo",), {}, ("foo", 3)),
        ({}, ("foo", 3), {}, ("foo", 3)),
        ({}, ("foo",), {"arg2": 3}, ("foo", 3)),
        ({}, (), {"arg1": "foo", "arg2": 3}, ("foo", 3)),
        # kwargs override dict
        ({"arg1": "foo", "arg2": 3}, (), {"arg1": "bar", "arg2": 5}, ("bar", 5)),
    ],
)
def test_cold_call_basic_signature(dct, a, kw, expected):
    def testfunc(arg1: str, arg2: int) -> tuple[str, int]:
        return arg1, arg2

    assert cold_call(testfunc, *a, dct=dct, **kw) == expected


@pytest.mark.parametrize(
    "dct, a, kw, error_cls, match",
    [
        # Arg is passed both positionally and by keyword
        ({"arg1": "foo"}, (3,), {}, TypeError, "multiple values for argument 'arg1'"),
        ({}, (3,), {"arg1": "foo"}, TypeError, "multiple values for argument 'arg1'"),
        (
            {"arg1": "foo", "arg2": 3},
            ("bar",),
            {},
            TypeError,
            "multiple values for argument 'arg1'",
        ),
        (
            {"arg1": "foo", "arg2": 3},
            ("bar", 9),
            {},
            TypeError,
            "multiple values for argument 'arg1'",
        ),
        (
            {"arg1": "foo"},
            (),
            {},
            TypeError,
            "missing 1 required positional argument: 'arg2'",
        ),
    ],
)
def test_cold_call_fails_basic_signature(dct, a, kw, error_cls, match):
    def testfunc(arg1: str, arg2: int) -> tuple[str, int]:
        return arg1, arg2

    with pytest.raises(error_cls, match=match):
        cold_call(testfunc, *a, dct=dct, **kw)
