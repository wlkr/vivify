from __future__ import annotations

from configparser import ConfigParser

from vivify import Vivifiable, Vivifier


class V(list[int], Vivifiable):
    @classmethod
    def vivify(cls, object):
        return cls(map(int, object.split(",")))


class A(object):
    b: B


class B(object):
    a: A
    v: V


# initialise the config parser and read the ini file
config = ConfigParser()
with open("example.ini") as f:
    config.read_file(f)

# specify the valid objects for vivification
vivifier = Vivifier(types=[A, B])
vivified = vivifier.vivify(instances="main", config=config)

# verify that the vivification occurred as expected
assert isinstance(vivified["foo"], A)
assert isinstance(vivified["bar"], B)
assert vivified["foo"].b == vivified["bar"]
assert vivified["bar"].a == vivified["foo"]
assert vivified["bar"].v == [1, 2, 3]
