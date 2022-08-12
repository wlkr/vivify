# Contributing

Thanks for taking the time to contribute! ❤️

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalise your pull requests.

## Table of Contents

- [Conduct](#conduct)
- [Dependencies](#dependencies)
- [Conventions](#conventions)
  - [Code](#code)
  - [Documentation](#documentation)
- [Testing](#testing)
- [Commits](#commits)
- [Versioning](#versioning)

## Conduct

We have a [Code of Conduct](CODE_OF_CONDUCT.md) which corresponds to the [Contributor Covenant](https://www.contributor-covenant.org/). Please follow it in all your interactions with the project.

## Dependencies

Vivify uses [Poetry](https://python-poetry.org/) for dependency and package management. You can use Poetry to fetch the repositories into a local virtual environment for development with `poetry install`. The virtual environment can then be run using `poetry shell`. If you are unfamiliar with Poetry then please see the [documentation](https://python-poetry.org/docs/) for more usage guidance.

## Conventions

### Code

In order to have a consistent source base, Vivify makes use of automated tools to make code conformity easier. Python source code MUST be formatted using [Black](https://github.com/psf/black), albeit with a maximum line length of 79 characters (per [PEP 8](https://peps.python.org/pep-0008/)). Type hinting SHOULD be used wherever reasonable.

### Documentation

Documentation comments MUST be formatted according to the [Google style](https://google.github.io/styleguide/pyguide.html).

## Testing

For any new or altered code, you MUST amend or add new relevant unit tests in the `tests` directory. These can be run with `pytest` to ensure that your tests have suitable coverage and pass successfully.

```shell
pytest --cov --cov-report html
```

## Commits

Git commits MUST use the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) style. Pull requests into the main branch will be squash merged so need to have a single, clear focus, otherwise multiple, separate pull requests should be made.

## Versioning

Vivify adheres to [semantic versioning](https://semver.org/spec/v2.0.0.html). Changes are documented in the [changelog](CHANGELOG.md) using the principles of the [Keep a Changelog project](https://keepachangelog.com/en/1.0.0/).
