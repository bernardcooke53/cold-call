# cold-call

[![PyPI - Version](https://img.shields.io/pypi/v/cold-call.svg)](https://pypi.org/project/cold-call)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cold-call.svg)](https://pypi.org/project/cold-call)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-Commit Enabled](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Give Python functions your unsolicited input. `cold-call` is implemented in pure
Python, fully type-annotated, and has zero runtime dependencies.

---

## Table of Contents

- [Installation](#installation)
- [License](#license)
- [Usage](#usage)

## Installation

```console
pip install cold-call
```

## License

`cold-call` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.

## Usage

`cold-call` enables you to throw any `dict` that you like at an arbitrary function,
and call that function using the _keys_ which match the corresponding _parameter_
names of the function to provide values. For example:

```python

from cold_call import cold_call

def func(a: int, b: str) -> None:
    print(a, b)

data = {"a": 5, "b": "foo"}

# prints "5 foo"
cold_call(func, dct=data)
```

On its own, this isn't very interesting - the same can be achieved with
the builtin unpack operator (`**{"a": 1, ...}`):

```python
# prints "5 foo"
func(**data)
```

However, `cold_call` enables you to pass a `dict` containing _additional_ keys,
which aren't in the function's parameter spec:

```python
data["c"] = 73
# prints "5 foo"
cold_call(func, dct=data)

# TypeError: func() got an unexpected keyword argument 'c'
func(**data)
```

This is similar to JavaScript's ability to [destructure an object passed
into the function using the function's parameter spec](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions#function_parameters).
The following two code examples are equivalent:

```javascript
const foo({name, age}) => {
    console.log(`${name}: ${age}`);
};

// prints "Joe: 30"
foo({
    name: "Joe",
    age: 30,
    birthday: "01/06/1990"
})
```

```python
def foo(name: str, age: int) -> None:
    print(f"{name}: {age}")

# prints "Joe: 30"
cold_call(
    foo,
    dct={
        "name": "Joe",
        "age": 30,
        "birthday": "01/06/1990"
    },
)
```

The `cold_call` function can be called with a `dict` _and_ additional
positional and keyword arguments; the values of these arguments are
used in preference to those found in the `dict`:

```python
def foo(name: str, age: int) -> None:
    print(f"{name}: {age}")

# prints "Joe: 42"
cold_call(
    foo,
    dct={"name": "Joe", "age": 21},
    age=42
)
```

`cold_call` also works with functions that have more specific signatures:

```python
def picky(
    a: str,
    /,
    b: int,
    *,
    c: bool,
) -> int:
    print(f"{a=}, {b=}, {c=}")
    return b * 2

# prints "a=gotcha, b=5, c=False"
x = cold_call(
    picky,
    5,
    dct={"a": "gotcha"},
    c=False,
)
assert x == 10
```

### `ColdCaller`

`cold-call` also provides a convenience class for use with the standard-library `dataclasses`.
This class implements a single method, `call`, which allows you to run `cold_call`
on a function with the data that the dataclass instance stores:

```python
from dataclasses import dataclass

from cold_call import ColdCaller

def user_action(name: str) -> None:
    print(f"user {name} is doing things!")

def is_authorized(name: str, is_admin: bool) -> bool:
    if not is_admin:
        print(f"forbidden: user {name} is not an admin")
    return is_admin and name != "Steve"  # Steve is banned


@dataclass
class User(ColdCaller):
    name: str
    age: int
    is_admin: bool = False


joe = User(name="Joe", age=30)

# prints "user Joe is doing things!"
joe.call(user_action)

# prints "forbidden: user Joe is not an admin"
joe.call(is_authorized)

# prints "True"
print(joe.call(is_authorized, is_admin=True))
```
