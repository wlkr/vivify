"""Complex vivification involving references between objects.

- Alice has a red car
- Bob has a blue car
- Carol does not own a car
- The green car is not owned by anybody"""

from __future__ import annotations
from configparser import ConfigParser
from typing import Any, Optional

from vivify import Vivifiable, Vivifier


class HexColour(Vivifiable):
    colour: int

    def __init__(self, colour) -> None:
        self.colour = colour

    @classmethod
    def vivify(cls, object: Any) -> Any:
        return cls(int(object[1:], 16))


class Car(object):
    colour: HexColour
    owner: Optional[Person]


class Person(object):
    name: str
    car: Optional[Car]


# read in the data from the config file
# allow_no_value=True allows for the empty optional attributes to be none
config: ConfigParser = ConfigParser(allow_no_value=True)
config.read_string(
    """
    [main]
    red_car = Car
    green_car = Car
    blue_car = Car
    alice = Person
    bob = Person
    carol = Person

    [DEFAULT]
    colour = #ff0000

    [red_car]
    owner = alice

    [green_car]
    colour = #00ff00
    owner = bob

    [blue_car]
    colour = #0000ff
    owner

    [alice]
    name = Alice
    car = red_car

    [bob]
    name = Bob
    car = green_car

    [carol]
    name = Carol
    car
"""
)

# create a vivifier and use it to vivify the groups
vivifier: Vivifier = Vivifier(types=[Car, Person])
objects = vivifier.vivify(instances="main", config=config, defaults="DEFAULT")

# we have created 3 cars and 3 people
assert len(objects) == 6
assert set(objects.keys()) == {
    "red_car",
    "green_car",
    "blue_car",
    "alice",
    "bob",
    "carol",
}
assert isinstance(objects["red_car"], Car)
assert isinstance(objects["green_car"], Car)
assert isinstance(objects["blue_car"], Car)
assert isinstance(objects["alice"], Person)
assert isinstance(objects["bob"], Person)
assert isinstance(objects["carol"], Person)
# the attributes have the correct references
assert objects["alice"].car == objects["red_car"]
assert objects["red_car"].owner == objects["alice"]
assert objects["bob"].car == objects["green_car"]
assert objects["green_car"].owner == objects["bob"]
assert objects["carol"].car is None
assert objects["blue_car"].owner is None
# other attributes have also been set correctly
assert isinstance(objects["red_car"].colour, HexColour)
assert objects["red_car"].colour.colour == int(0xFF0000)
assert isinstance(objects["green_car"].colour, HexColour)
assert objects["green_car"].colour.colour == int(0x00FF00)
assert isinstance(objects["blue_car"].colour, HexColour)
assert objects["blue_car"].colour.colour == int(0x0000FF)
assert objects["alice"].name == "Alice"
assert objects["bob"].name == "Bob"
assert objects["carol"].name == "Carol"
