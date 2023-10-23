from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from functools import wraps
from inspect import Parameter, signature
from itertools import groupby
from typing import Any, Callable, TypeVar

__version__ = "0.1.0"

log = logging.getLogger(__name__)
T = TypeVar("T")


def cold_call(
    func: Callable[..., T],
    *a: Any,
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
    >>> cold_call(foo, **d)
    bar True
    """
    log.debug("Binding arguments for %r", func.__qualname__)

    sig = signature(func, follow_wrapped=__follow_wrapped)

    grouped_by_kind = {
        kind: dict(items)
        for kind, items in groupby(sig.parameters.items(), lambda p: p[1].kind)
    }

    # If we have a VAR_KEYWORD arg, we have to put all the non-named parameters
    # into it. So let's see what's left over at the end and bind it to that.
    posonly_args = grouped_by_kind.get(Parameter.POSITIONAL_ONLY)
    pos_or_kwargs = grouped_by_kind.get(Parameter.POSITIONAL_OR_KEYWORD)
    var_posarg = grouped_by_kind.get(Parameter.VAR_POSITIONAL)
    grouped_by_kind.get(Parameter.KEYWORD_ONLY)
    var_kwarg = grouped_by_kind.get(Parameter.VAR_KEYWORD)

    ######
    # Positional-only arguments

    # For positional-only args, the following precedence applies:
    #    1) Any named arguments passed as keyword-arguments which
    #       match the param names of positional-only arguments are
    #       passed there
    #    2) Any arguments passed positionally are used to fill the
    #       remaining positional arguments, until they're all filled
    #    3) Leftover arguments are ignored if there's no VAR_POSITIONAL
    #       argument, or passed into this VAR_POSITIONAL argument
    #
    # Therefore the main logic here is to find any "known" posargs and their indices,
    # and ensure that the others are populated from the positional arguments.
    ######

    args: list[Any] = []
    passed_posargs = list(a)

    if posonly_args:
        for index, name in enumerate(posonly_args):
            if name in kw:
                args.append(kw[name])
            elif passed_posargs:
                value, *passed_posargs = passed_posargs
                args.append(value)
            elif (default := posonly_args[name].default) is not Parameter.empty:
                args.append(default)
            else:
                # no more positional arguments given
                # NOTE: this is _almost_ identical to how the inbuilt errors for missing
                # arguments are reported to the user, but this indicates if positional
                # arguments are missing when others have been filled by keyword
                # arguments.

                # For example:
                # def f(arg1, arg2): pass  # noqa: ERA001
                #
                # if we were to call cold_call(f, arg2=5), the inbuilt error would be
                # TypeError("f() missing 1 required positional argument: 'arg2'")  # noqa: ERA001,E501
                # But of course the user _has_ supplied arg2, it's arg1 that's missing.
                # Our error is:
                # TypeError("f() missing 1 required positional argument: 'arg1'")  # noqa: ERA001,E501

                unfilled_posargs = list(posonly_args)[index:]
                one_missing = len(unfilled_posargs) == 1

                msg = (
                    f"{func.__qualname__}() missing {len(unfilled_posargs)} required "
                    + (
                        f"positional argument: {unfilled_posargs[0]!r}"
                        if one_missing
                        else f"positional arguments: {', '.join(repr(name) for name in unfilled_posargs[:-1])} "  # noqa: E501
                        f"and {unfilled_posargs[-1]!r}"
                    )
                )
                raise TypeError(msg)

    #####
    # Positional-or-keyword arguments
    # Find any that we can from the keyword arguments, and fill in the rest
    # from the positional arguments.
    # If a parameter can be passed positionally or by keyword,
    # we prefer to pass it positionally as otherwise we can get
    # 'multiple values' for parameter
    #####
    if pos_or_kwargs:
        for index, name in enumerate(pos_or_kwargs):
            if name in kw:
                # if we can supply by keyword then we will
                args.append(kw[name])
            elif passed_posargs:
                value, *passed_posargs = passed_posargs
                args.append(value)
            elif (default := pos_or_kwargs[name].default) is not Parameter.empty:
                args.append(default)
            else:
                # no more positional arguments given
                # similar to posonly_args above
                unfilled_pos_or_kwargs = list(pos_or_kwargs)[index:]
                one_missing = len(unfilled_pos_or_kwargs) == 1
                msg = (
                    f"{func.__qualname__}() missing {len(unfilled_pos_or_kwargs)} required "  # noqa: E501
                    + (
                        f"positional argument: {unfilled_pos_or_kwargs[0]!r}"
                        if one_missing
                        else f"positional arguments: {', '.join(repr(name) for name in unfilled_pos_or_kwargs[:-1])} "  # noqa: E501
                        f"and {unfilled_pos_or_kwargs[-1]!r}"
                    )
                )
                raise TypeError(msg)

    #####
    # Variadic positional argument
    #####
    if var_posarg:
        args.extend(passed_posargs)

    #####
    # Keyword-only arguments
    #####
    kwargs = {
        name: kw[name]
        for name in grouped_by_kind.get(Parameter.KEYWORD_ONLY, {})
        if name in kw
    }

    #####
    # Variadic Keyword arguments
    #####
    if var_kwarg:
        kwargs.update({name: value for name, value in kw.items() if name not in kwargs})

    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    log.debug("Bound args and kwargs for function %r", func.__qualname__)

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
        This method uses cold_call with `self` as the input kwargs.
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

        Note that this means positional arguments to this method will
        be overridden by dataclass fields on `self`.
        """
        return cold_call(func, *a, **{**asdict(self), **kw})
