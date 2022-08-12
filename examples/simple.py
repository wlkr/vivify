"""Simple vivification example.

Let's say we want to model the following mathematical puzzle and have created a
class to represent each person:

Bob is 24. He is twice as old as Alice was when Bob was as old as Alice is now.
How old is Alice?

https://www.daviddarling.info/encyclopedia/A/age_puzzles_and_tricks.html"""

from configparser import ConfigParser
from typing import Optional

from vivify import Vivifier


class Person(object):
    """Minimal representation of a Person for a logic puzzle."""

    name: str
    age: Optional[int]


# read in the data from the config file
# note that allow_no_value=True allows for the empty optional age to be none
config: ConfigParser = ConfigParser(allow_no_value=True)
config.read_string(
    """
    [main]
    alice = Person
    bob = Person

    [alice]
    name = Alice
    age

    [bob]
    name = Bob
    age = 24
    """
)

# setup the vivifier to allow creating new people
vivifier: Vivifier = Vivifier(types=[Person])
# turn the configuration data into instances of person
people = vivifier.vivify(instances="main", config=config)

# people now contains the two instances of person with the specified keys
assert len(people) == 2
assert set(people.keys()) == {"alice", "bob"}

# the classes have been instantiated with the data from the config
assert isinstance(people["alice"], Person)
assert people["alice"].name == "Alice"
assert people["alice"].age is None
assert isinstance(people["bob"], Person)
assert people["bob"].name == "Bob"
assert people["bob"].age == 24
