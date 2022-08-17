"""Vivify is a library for instantiating objects from INI file style configs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from configparser import DEFAULTSECT
from logging import Logger, NullHandler, getLogger
from typing import (
    Any,
    Callable,
    Final,
    Iterable,
    Mapping,
    Optional,
    TypeVar,
    Union,
    get_type_hints,
)

from typing_extensions import get_args
from typing_inspect import (
    is_union_type,
)

__author__ = "Adam D Walker"
__copyright__ = "Copyright 2022 " + __author__
__credits__ = [__author__]
__email__ = "adam@wlkr.dev"
__license__ = "Apache-2.0"
__maintainer__ = __author__
__status__ = "Development"
__version__ = "1.0.1"

# setup logging
log: Logger = getLogger(__name__)
log.addHandler(NullHandler())

INSTANCE_SECTION: Final[str] = "vivify"

T = TypeVar("T")


def entry_exit_logging(function: Callable[..., T]) -> Callable[..., T]:
    """Wrap a function with entry and exit debug logging.

    Args:
        function (Callable[..., Any]): Function to wrap.

    Returns:
        Callable[..., Any]: Wrapped function.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapped logged function.

        Returns:
            Any: Result of calling the wrapped function.
        """
        log.debug(
            f"Calling {function.__name__!r} with args {args!r} and kwargs"
            f" {kwargs!r}"
        )
        result = function(*args, **kwargs)
        log.debug(f"Returning value {result!r} from {function.__name__!r}")
        return result

    return wrapper


# convenience config types
Config = Mapping[str, Mapping[str, Any]]


class VivificationError(Exception):
    """Wrapper exception for issues relating to the vivify library."""

    pass


class Vivifiable(ABC):
    """Mixin class for objects which can be instantiated during vivification.

    Custom types which take a single argument from a configuration must
    override the vivify method to instantiate the class. This is useful for
    configuration from an INI file using a ConfigParser which will only provide
    a string for all values."""

    @classmethod
    @abstractmethod
    @entry_exit_logging
    def vivify(cls, object: Any) -> Any:
        """Constructor for create an instance from a configuration value.

        Args:
            object (Any): Value to use to instantiate the class.

        Returns:
            Any: Instantiated class or converted type.
        """
        pass  # pragma: no cover


class Vivifier(object):
    """Handle vivification of objects from configurations."""

    @entry_exit_logging
    def __init__(self, types: Iterable[type]) -> None:
        """Create a new vivifier instance.

        Args:
            types (Iterable[Type]): Valid types for vivification.
        """
        self.types: Mapping[str, type]
        if types:
            self.types = {t.__name__: t for t in types}
        else:
            log.warning("Instantiating Vivifier with no valid types")
            self.types = {}

    @entry_exit_logging
    def _extract_configs(
        self, config: Config, instances: Optional[str], defaults: Optional[str]
    ) -> Config:
        """Extract the complete configurations for each object.

        Configuration objects must have a section which provides a mapping from
        variable name to type name. An optional default section can also be
        used, as is the case with a ConfigParser. This method extracts the
        complete configuration for each named object, integrating any defaults.

        Args:
            config (Config): Configuration for all objects.
            instances (Optional[str]): Name key of the instance section.
            defaults (Optional[str]): Name key of the default section.

        Returns:
            Config: Extracted configuration.
        """
        return {
            s: {
                **(config[defaults] if defaults and defaults in config else {}),
                **config[s],
            }
            for s in config
            if s and s != instances and s != defaults
        }

    @entry_exit_logging
    def _process_attributes(
        self,
        instances: Mapping[str, str],
        config: Config,
        vivified: Mapping[str, Any],
    ) -> Iterable[tuple[str, str, Any]]:
        """Process all instance attributes specified in the configuration.

        This will attempt to create a list of values to be assigned to
        attributes and may include duplicate attributes with different values in
        the case of union or optional types, e.g. Union[int, str] with config
        entry 1 would include the string and integer versions.

        Args:
            instances (Mapping[str, str]): Instance names and types.
            config (Config): Instance attribute configuration.
            vivified (Mapping[str, Any]): Already vivified objects.

        Raises:
            VivificationException: On failure to assign all attributes.

        Returns:
            Iterable[tuple[str, str, Any]]: Processed attributes for adding.
        """
        types = {k: get_type_hints(v) for k, v in self.types.items()}
        queue: deque[tuple[str, str, str, Optional[type]]] = deque(
            (
                (i, a, v, types[instances[i]].get(a, None))
                for i, c in config.items()
                for a, v in c.items()
                if i in instances
            )
        )
        log.debug(f"Attribute processing queue initialised as {queue!r}")
        queue_length: int = len(queue)
        setters: Iterable[tuple[str, str, Any]] = []
        seen: set[tuple[str, str]] = set()
        while queue:
            # fetch an instance's attribute data from the queue
            t: Optional[type]
            i, a, v, t = queue.pop()
            log.info(
                f"Handling attribute {t!r} for instance {i!r} with value"
                f" {v!r} and type {t!r}"
            )

            # for unions add the attribute with all possible types to the queue
            if is_union_type(t):
                log.debug(f"Expanding and adding union type {t!r}")
                queue.extend((i, a, v, t) for t in get_args(t))
                continue

            # filter out any unsupported generic types
            try:
                if t is not None and isinstance(Any, t):
                    pass
            except TypeError:
                log.warning(
                    f"Cannot add attribute with unsupported generic type {t!r}"
                )
                continue

            # handle untyped attributes
            if t is None:
                log.warning(
                    f"Adding untyped attribute {a!r} with value {v!r} to"
                    f" instance {i!r}"
                )
                setters.append((i, a, v))
                seen.add((i, a))
            # handle none for optional types
            elif t is type(None):  # noqa: E721
                if v is None:
                    log.debug(
                        f"Adding attribute {a!r} to instance {i!r} with"
                        f" optional value {v!r} matching type {t!r}"
                    )
                    setters.append((i, a, None))
                    seen.add((i, a))
                else:
                    log.warning(
                        f"Cannot add attribute {a!r} to instance {i!r} with"
                        f" value {v!r} because optional type does not match"
                        f" {t!r}"
                    )
            # value already matches annotated type
            elif isinstance(v, t):
                log.debug(
                    f"Adding attribute {a!r} to instance {i!r} with value {v!r}"
                    f" for matching type {t!r}"
                )
                setters.append((i, a, v))
                seen.add((i, a))
            # type is vivifiable
            elif issubclass(t, Vivifiable):
                log.debug(
                    f"Adding vivifiable attribute {a!r} with type {t!r} and"
                    f" value {v!r} to instance {i!r}"
                )
                setters.append((i, a, t.vivify(v)))
                seen.add((i, a))
            # type is a reference
            elif (
                isinstance(v, str)
                and v in vivified
                and isinstance(vivified[v], t)
            ):
                log.debug(
                    f"Adding attribute {a!r} to instance {i!r} with reference"
                    f" to instance {v!r}"
                )
                setters.append((i, a, vivified[v]))
                seen.add((i, a))
            # attempt to coerce the type
            else:
                try:
                    log.debug(
                        f"Adding attribute {a!r} with value {v!r} to instance"
                        f" {i!r} via coercion to type {t!r}"
                    )
                    setters.append((i, a, t(v)))
                    seen.add((i, a))
                except (TypeError, ValueError):
                    log.warning(
                        f"Failed to add attribute {a!r} to instance {i!r} with"
                        f" value {v!r} via coercion to type {t!r}"
                    )

        # verify that the correct number of possible attributes have been set
        if len(seen) < queue_length:
            raise VivificationError(
                f"Assigned {len(seen)} of {queue_length} attribute(s) to"
                " objects. Attribute types may not be suitable for vivification"
            )

        return setters

    @entry_exit_logging
    def _vivify(
        self,
        instances: Union[Mapping[str, str], str],
        config: Config,
        defaults: Optional[str] = DEFAULTSECT,
    ) -> Mapping[str, Any]:
        """Internal handler for vivifying objects.

        Args:
            instances (Union[Mapping[str, str], str]): Instances name type
                mapping or the name of the instances section in the supplied
                config.
            config (Config): Configuration data for attributes and optionally
                also instances.
            defaults (Optional[str], optional): Name of the default section in
                the config, if used. Defaults to DEFAULTSECT.

        Returns:
            Mapping[str, Any]: All vivified objects.
        """
        # store for vivified objects
        vivified: Mapping[str, Any] = {}
        # store for instances name and type data
        instances_config: Mapping[str, str]

        instances_is_str: bool = isinstance(instances, str)
        # get the instances data
        if instances_is_str:
            if instances in config:
                instances_config = config[instances]
            else:
                instances_config = {}
        else:
            instances_config = instances

        # extract just the attribute configuration data
        if defaults or instances_is_str:
            config = self._extract_configs(
                config=config,
                instances=instances if instances_is_str else None,
                defaults=defaults,
            )

        # create all objects and set the attributes
        vivified = {
            v: self.types[instances_config[v]]()
            for v in config
            if v in instances_config
        }
        seen: set[tuple[str, str]] = set()
        for instance, attribute, value in self._process_attributes(
            instances_config, config, vivified
        ):
            if (instance, attribute) not in seen:
                seen.add((instance, attribute))
                setattr(vivified[instance], attribute, value)
        return vivified

    @entry_exit_logging
    def vivify(
        self,
        instances: Union[Mapping[str, str], str],
        config: Config,
        defaults: Optional[str] = DEFAULTSECT,
    ) -> Mapping[str, Any]:
        """Vivify the specified objects.

        Args:
            instances (Union[Mapping[str, str], str]): Instances name type
                mapping or the name of the instances section in the supplied
                config.
            config (Config): Configuration data for attributes and optionally
                also instances.
            defaults (Optional[str], optional): Name of the default section in
                the config, if used. Defaults to DEFAULTSECT.

        Returns:
            Mapping[str, Any]: All vivified objects.
        """
        try:
            return self._vivify(
                instances=instances, config=config, defaults=defaults
            )
        except VivificationError:
            raise
        except Exception as error:
            raise VivificationError(
                "Error occurred during vivification."
            ) from error
