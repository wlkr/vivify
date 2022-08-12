"""Vivifiable example.

Unlike other common configuration file types, such as JSON, TOML, and YAML, in
INI files every value is interpreted as a string. This is acceptable for
primitive coercible types (e.g. integers and strings) but doesn't inherently
allow for for more complex types. This small example shows how we can use the
Vivifiable mixin to support more complex types.
"""

from configparser import ConfigParser
from typing import Any

from vivify import Vivifiable, Vivifier


class Names(list[str], Vivifiable):
    """Simple vivifiable string list."""

    SEPARATOR: str = ","

    @classmethod
    def vivify(cls, object: Any) -> Any:
        return cls(map(str.strip, object.split(Ages.SEPARATOR)))


class Ages(list[int], Vivifiable):
    """Simple vivifiable integer list."""

    SEPARATOR: str = ","

    @classmethod
    def vivify(cls, object: Any) -> Any:
        return cls(map(int, object.split(Ages.SEPARATOR)))


class People(object):
    """Simple class for storing basic people's data."""

    names: Names
    ages: Ages


# read in the data from the config file
config: ConfigParser = ConfigParser()
config.read_string(
    """
    [main]
    group_1 = People

    [group_1]
    names = Alice, Bob, Carol, Dave
    ages = 1, 2, 3, 4
    """
)

# create a vivifier and use it to vivify the groups
vivifier: Vivifier = Vivifier(types=[People])
groups = vivifier.vivify(instances="main", config=config)

# people now contains the one group from the configuration data
assert len(groups) == 1
assert set(groups.keys()) == {"group_1"}

# the classes has been instantiated with provided data
assert isinstance(groups["group_1"], People)
# ages is a list of numbers
assert isinstance(groups["group_1"].ages, Ages)
assert groups["group_1"].ages == [1, 2, 3, 4]
# names is a list of strings
assert isinstance(groups["group_1"].names, Names)
assert groups["group_1"].names == ["Alice", "Bob", "Carol", "Dave"]
