from __future__ import annotations

from configparser import ConfigParser
from typing import Any, Mapping, Optional, Union

import pytest
from vivify.vivify import Vivifiable, VivificationError, Vivifier


def test_vivify__extract_configs():
    """Test extraction of instance's parameters from a configuration."""
    # check extraction from a dictionary based config
    assert Vivifier(types=[])._extract_configs(
        config={
            "main": {"foo": "A", "bar": "B"},
            "DEFAULT": {"x": "0"},
            "foo": {"x": "1"},
            "bar": {},
        },
        instances="main",
        defaults="DEFAULT",
    ) == {"foo": {"x": "1"}, "bar": {"x": "0"}}

    # check extraction from a configparser
    config: ConfigParser = ConfigParser()
    config.read_string(
        """
        [main]
        foo = a
        bar = a
        [DEFAULT]
        x = 0
        [foo]
        x = 1
        [bar]
        """
    )
    assert Vivifier(types=[])._extract_configs(
        config=config, instances="main", defaults="DEFAULT"
    ) == {
        "foo": {"x": "1"},
        "bar": {"x": "0"},
    }

    # check empty args
    assert (
        Vivifier(types=[])._extract_configs(
            config={},
            instances="",
            defaults="",
        )
        == {}
    )

    # check with impractical instances and defaults
    assert (
        Vivifier(types=[])._extract_configs(
            config={"a": {"a.a": "1"}, "b": {"b.b": "2"}},
            instances="a",
            defaults="b",
        )
        == {}
    )
    assert Vivifier(types=[])._extract_configs(
        config={"a": {"a.a": "1"}, "b": {"b.b": "2"}},
        instances="a",
        defaults="a",
    ) == {"b": {"a.a": "1", "b.b": "2"}}


class TestEmpty(object):
    pass


def test_vivify__process_attributes_empty():
    """Test setting non-existant attributes."""
    assert Vivifier([TestEmpty])._process_attributes(
        instances={"test_empty": "TestEmpty"},
        config={"test_empty": {"attribute": "test"}},
        vivified={},
    )


def test_vivify__process_attributes_same():
    """Test setting attributes of the same type as in the configuration."""

    class TestString(object):
        string: str

    assert Vivifier([TestString])._process_attributes(
        instances={"test_string": "TestString"},
        config={"test_string": {"string": "1"}},
        vivified={},
    ) == [("test_string", "string", "1")]


def test_vivify__process_attributes_coercible():
    """Test setting coercible attributes."""

    class TestInteger(object):
        integer: int

    assert Vivifier([TestInteger])._process_attributes(
        instances={"test_integer": "TestInteger"},
        config={"test_integer": {"integer": "1"}},
        vivified={},
    ) == [("test_integer", "integer", 1)]


class TestVivifiableTuple(Vivifiable):
    @classmethod
    def vivify(cls, object: str) -> tuple[int]:
        return tuple(map(int, object.split(",")))


def test_vivify__process_attributes_vivifiable():
    """Test setting vivifiable attributes."""

    class TestVivifiable(object):
        vivifiable: TestVivifiableTuple

    assert Vivifier([TestVivifiable])._process_attributes(
        instances={"test_vivifiable": "TestVivifiable"},
        config={"test_vivifiable": {"vivifiable": "1, 2, 3, 4"}},
        vivified={},
    ) == [("test_vivifiable", "vivifiable", (1, 2, 3, 4))]


def test_vivify__process_attributes_union():
    """Test setting union and optional attributes"""

    # check complex union type
    class TestUnion(object):
        union: Union[Optional[int], str, TestVivifiableTuple]

    assert set(
        Vivifier([TestUnion])._process_attributes(
            instances={"test_union": "TestUnion"},
            config={"test_union": {"union": "100"}},
            vivified={},
        )
    ) == set(
        [
            ("test_union", "union", 100),
            ("test_union", "union", "100"),
            ("test_union", "union", (100,)),
        ]
    )

    # check nonetype is handled for empty optional values
    class TestOptionalString(object):
        optional: Optional[str]

    assert Vivifier([TestOptionalString])._process_attributes(
        instances={"test_optional_string": "TestOptionalString"},
        config={"test_optional_string": {"optional": ""}},
        vivified={},
    ) == [("test_optional_string", "optional", "")]
    assert Vivifier([TestOptionalString])._process_attributes(
        instances={"test_optional_string": "TestOptionalString"},
        config={"test_optional_string": {"optional": None}},
        vivified={},
    ) == [
        ("test_optional_string", "optional", None),
        ("test_optional_string", "optional", "None"),
    ]

    class TestOptionalInteger(object):
        optional: Optional[int]

    with pytest.raises(VivificationError):
        Vivifier([TestOptionalInteger])._process_attributes(
            instances={"test_optional_integer": "TestOptionalInteger"},
            config={"test_optional_integer": {"optional": ""}},
            vivified={},
        )


class TestReference(object):
    reference: TestReference


def test_vivify__process_attributes_reference():
    """Test setting reference attributes."""

    test_reference_a: TestReference = TestReference()
    test_reference_b: TestReference = TestReference()
    assert set(
        Vivifier([TestReference])._process_attributes(
            instances={
                "test_reference_a": "TestReference",
                "test_reference_b": "TestReference",
            },
            vivified={
                "test_reference_a": test_reference_a,
                "test_reference_b": test_reference_b,
            },
            config={
                "test_reference_a": {"reference": "test_reference_b"},
                "test_reference_b": {"reference": "test_reference_a"},
            },
        )
    ) == set(
        [
            ("test_reference_a", "reference", test_reference_b),
            ("test_reference_b", "reference", test_reference_a),
        ]
    )


def test_vivify__process_attributes_unsupported():
    """Test that processing fails correctly for unsupported attribute types."""

    class TestUnsupportedList(object):
        unsupported: list[int]

    with pytest.raises(VivificationError):
        Vivifier([TestUnsupportedList])._process_attributes(
            instances={"test_unsupported_list": "TestUnsupportedList"},
            config={"test_unsupported_list": {"unsupported": "test"}},
            vivified={},
        )

    class TestInvalidCoercion(object):
        invalid: TestEmpty

    with pytest.raises(VivificationError):
        Vivifier([TestInvalidCoercion])._process_attributes(
            instances={"test_invalid_coercion": "TestInvalidCoercion"},
            config={"test_invalid_coercion": {"invalid": "test"}},
            vivified={},
        )


class TestVivify(object):
    string: str
    integer: int
    vivifiable: TestVivifiableTuple
    reference: TestVivify


def test_vivify__vivify():
    """Test that the internal vivification function returns correct values."""
    # check for empty data
    assert (
        Vivifier(types=[])._vivify(instances={}, config={}, defaults="") == {}
    )
    assert (
        Vivifier(types=[])._vivify(
            instances="instances", config={}, defaults="DEFAULT"
        )
        == {}
    )

    # check for dict args
    vivified: Mapping[str, Any] = Vivifier(types=[TestVivify])._vivify(
        instances={"a": "TestVivify", "b": "TestVivify"},
        config={
            "a": {
                "string": "test",
                "integer": "1",
                "vivifiable": "1, 2, 3",
                "reference": "b",
            },
            "b": {
                "string": "test",
                "integer": "2",
                "vivifiable": "2",
                "reference": "a",
            },
        },
    )
    assert isinstance(vivified["a"], TestVivify)
    assert vivified["a"].string == "test"
    assert vivified["a"].integer == 1
    assert vivified["a"].vivifiable == (1, 2, 3)
    assert vivified["a"].reference == vivified["b"]
    assert isinstance(vivified["b"], TestVivify)
    assert vivified["b"].string == "test"
    assert vivified["b"].integer == 2
    assert vivified["b"].vivifiable == (2,)
    assert vivified["b"].reference == vivified["a"]

    # check for config parser style args
    config: ConfigParser = ConfigParser()
    config.read_string(
        """
        [main]
        a = TestVivify
        b = TestVivify
        [DEFAULT]
        string = test
        [a]
        integer = 1
        vivifiable = 1, 2, 3
        reference = b
        [b]
        integer = 2
        vivifiable = 2
        reference = a
        """
    )
    vivified = Vivifier(types=[TestVivify])._vivify(
        instances="main", config=config, defaults="DEFAULT"
    )


def test_vivify_vivify():
    """Test vivification."""
    # simple vivification function call test
    assert Vivifier(types=[]).vivify(instances={}, config={}, defaults="") == {}
    # test invalid missing instance for config
    assert (
        Vivifier(types=[])._vivify(
            instances={}, config={"a": {"integer": "A"}}, defaults=""
        )
        == {}
    )
    # test invalid missing config for instance
    assert (
        Vivifier(types=[])._vivify(instances={"a": "A"}, config={}, defaults="")
        == {}
    )

    # check unsupported type
    class TestUnsupportedList(object):
        unsupported: list[int]

    with pytest.raises(VivificationError):
        Vivifier([TestUnsupportedList]).vivify(
            instances={"test_unsupported_list": "TestUnsupportedList"},
            config={"test_unsupported_list": {"unsupported": "test"}},
            defaults="",
        )

    # check unsupported class
    class TestUnsupportedInteger(object):
        def __init__(self) -> None:
            self._integer = 0

        @property
        def integer(self):
            return self._integer  # pragma: no cover

        @integer.setter
        def integer(self, integer):
            raise Exception("Test fail attribute setting")

    with pytest.raises(VivificationError):
        Vivifier([TestUnsupportedInteger]).vivify(
            instances={"test_unsupported_integer": "TestUnsupportedInteger"},
            config={"test_unsupported_integer": {"integer": "1"}},
            defaults="",
        )
