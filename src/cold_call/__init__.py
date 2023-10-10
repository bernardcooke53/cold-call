from __future__ import annotations

import logging
from copy import copy
from dataclasses import asdict, dataclass
from functools import wraps
from inspect import Parameter, signature
from typing import Any, Callable, TypeVar

log = logging.getLogger(__name__)
T = TypeVar("T")


def cold_call(
    func: Callable[..., T],
    *a: Any,
    dct: dict[str, Any],
    __follow_wrapped: bool = True,
    **kw: Any,
) -> T:
    """
    This function enables a JavaScript-style spread of a dictionary so that only the
    required parameters end up being passed into the function. E.g.
    >>> d = {"foo": "bar", "baz": 7, "arg1": True}
    >>> def func(foo, arg2=False):
    ...     print(foo, arg2)
    ...
    >>> cold_call(foo, dct=d)
    bar True
    """
    # N.B. in this implementation, *a are always supplied positionally before any
    # keyword arguments. This means you can't specify the value for the first
    # positional parameter in dct and collect other parameters via *a for example
    # - positional parameters should use *a or can be given in dct if *a is not used.

    # Take a shallow copy of dct to avoid mutating the original dict -
    # otherwise popping keys could affect usage elsewhere.
    # Doing a deep copy might be unexpected behaviour as user might expect the
    # same instances to be passed into multiple functions
    log.debug("Binding arguments for %r", func.__qualname__)

    tmp_kw = copy(dct)
    tmp_kw.update(kw)

    log.debug(
        "Binding arguments for %r: args - %s, kwargs - %s",
        func.__qualname__,
        str(a),
        str(tmp_kw),
    )
    sig = signature(func, follow_wrapped=__follow_wrapped)
    var_kwarg_name: Parameter | None = None
    permitted_kwargs: dict[str, Any] = {}

    for name, param in sig.parameters.items():
        if param.kind == Parameter.VAR_KEYWORD:
            # If we have a VAR_KEYWORD arg, we have to put all the non-named parameters
            # into it. So let's see what's left over at the end and bind it to that.
            var_kwarg_name = param
            continue
        if name in tmp_kw:
            # Use pop so that we know any remaining extra kwargs
            # can be put into the var_kwarg parameter at the end,
            # if there is one
            permitted_kwargs[name] = tmp_kw.pop(name)

    if var_kwarg_name is not None:
        # If we're allowed var_kwargs then we should give as many as possible -
        # all the left over parameters that haven't been popped go here
        permitted_kwargs.update(tmp_kw)

    bound = sig.bind_partial(*a, **permitted_kwargs)
    bound.apply_defaults()

    log.debug(
        "Bound args %s and kwargs %s for function %r",
        str(bound.args),
        str(bound.kwargs),
        func.__qualname__,
    )
    # if param can be pos or kw, pos preferred so needs args anyway
    return func(*bound.args, **bound.kwargs)


def cold_callable(f: Callable[..., T]) -> Callable[..., T]:
    @wraps(f)
    def _new_callable(*a: Any, **kw: Any) -> T:
        return cold_call(f, *a, **kw)

    return _new_callable


@dataclass
class ColdCaller:
    """
    Subclass with the required parameters - this provides a `call` method
    for JavaScript-style spread of parameters over a function
    """

    def call(self, func: Callable[..., T], *a: Any, **kw: Any) -> T:
        """
        This method uses cold_call with `self` as the input dict of params.
        E.g.
        >>> @dataclass
        ... class MyState(ColdCaller):
        ...     foo: str
        ...     bar: str
        ...     param1: bool = False
        ...     param2: bool = True
        ...
        >>> s = MyState("foo", "bar", param1=True)
        >>> def func(foo, param2, param3 = True):
        ...     print(foo, param2, param3)
        >>> s.call(func, param3 = False)
        foo True False
        """
        return cold_call(func, *a, dct=asdict(self), **kw)
