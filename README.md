# Vivify

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Keep a Changelog v1.1.0 badge](https://img.shields.io/badge/changelog-Keep%20a%20Changelog%20v1.1.0-%23E05735)](./CHANGELOG.md)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![img](https://img.shields.io/badge/semver-2.0.0-green)](https://semver.org/)

## Overview

Vivify is a lightweight Python library for INI style object initialisation. Using Vivify, you can instantiate classes and set attributes using values provided from an external configuration. Vivify supports both POD types as well as more complex objects and relationships. This is particularly useful in domains where the configuration is very closely coupled to the objects.

## Installation

Installing Vivify is easy! Vivify is available on the Python Packaging Index. If you're using Poetry then `poetry add vivify`, otherwise:

```shell
pip install vivify
```

## Usage

The snippets shown below are provided in full in the [examples directory](./examples/README.md) and demonstrate using an external configuration to instantiate some pre-defined classes. Further examples are also supplied in the examples directory.

This example showcases how Vivify supports complex relationships between classes. In this case, there is a bidirectional associative relationship between classes `A` and `B` and `B` has an additional variable of type `V`.

```python
class V(list[int], Vivifiable):
    @classmethod
    def vivify(cls, object):
        return cls(map(int, object.split(",")))


class A(object):
    b: B


class B(object):
    a: A
    v: V
```

Note that in the code above we should specify the types of any instance variables. This is so that Vivify can instantiate the correct type for a specified variable, e.g. to distinguish between a string and a reference to another object in the configuration. It is also important that any attributes specified in the configuration should be settable (or at the very least an attempt to set the attribute should not fail).

The following configuration INI file (`example.ini`) contains the options we want to use to instantiate two instances of these classes named `foo` and `bar`.

```ini
[main]
foo = A
bar = B

[foo]
i = 1
b = bar

[bar]
a = foo
v = 1, 2, 3
```

The `main` section where variables are named can be given any valid section name other than that which is reserved for supplying default values for sections - this is defined as `"DEFAULT"` in the standard [configuration file parsing library](https://docs.python.org/3/library/configparser.html). Note how the other section names correspond to the variable names provided in the `main` section.

```python
# initialise the config parser and read the ini file
config = ConfigParser()
with open("example.ini") as f:
    config.read_file(f)

# specify the valid objects for vivification
vivifier = Vivifier(types=[A, B])
vivified = vivifier.vivify(instances="main", config=config)
```

```python
# verify that the vivification occurred as expected
assert isinstance(vivified["foo"], A)
assert isinstance(vivified["bar"], B)
assert vivified["foo"].b == vivified["bar"]
assert vivified["bar"].a == vivified["foo"]
assert vivified["bar"].v == [1, 2, 3]
```

## Limitations

Most simple cases should work without issue. Things get complicated and more care should be taken when there are multiple possible types for a value. Consider an attribute with the type annotation `Union[list[int], Optional[str]]`. With a configuration value of `None`, there are two possible ways this could be interpreted: (i) `None`, and (ii) `"None"` (because `str(None)` returns `"None"`). The `list[int]` annotation will be skipped because it is a parameterised generic and cannot be instantiated. Currently, the actual type chosen for the is entirely dependent on the ordering of the result of a call to `get_args` from the [typing extensions](https://github.com/python/typing_extensions) library. The first valid matching type is picked for setting the attributes value.

```python
from typing import Optional, Union
from typing_extensions import get_args

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

assert (
    str(get_args(Union[list[int], Optional[str]]))
    == "(list[int], <class 'str'>, <class 'NoneType'>)"
)
```

In this case, the value would be set to the string `"None"` because this matches first (after the invalid `list[int]`) and the permissive `str` type coercion accepts None as an argument.

If you are especially concerned about which type is used then it is a good idea to either make the typing more strict or use `Vivifiable` objects (preferred approaches) or alternatively check a call to `get_args` yourself on the type to verify that the implementation will work as you expect. Vivify provides extensive logging so you can see how variables are handled internally.

## Licence

Copyright © 2022 [Adam D Walker](mailto:adam@wlkr.dev)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at <http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
