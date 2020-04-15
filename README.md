[![PyPI version](https://badge.fury.io/py/semeio.svg)](https://badge.fury.io/py/semeio)
[![Build Status](https://travis-ci.com/equinor/semeio.svg?branch=master)](https://travis-ci.com/equinor/semeio)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# semeio #

Jobs and workflow jobs used in [ERT](https://github.com/equinor/ert).

## Run tests
[tox](https://tox.readthedocs.io/en/latest/) is used as the test facilitator,
to run the full test suite:

```sh
# Test
pip install tox
tox
```

or to run it for a particular Python version (in this case Python 3.7):

```sh
# Test
pip install tox
tox -e py37
```

[pytest](https://docs.pytest.org/en/latest/) is used as the test runner, so for quicker
iteration it is possible to run:

```sh
# Test
pytest
```

this requires that the test dependencies from `test_requirements.txt` are installed.

```sh
# Install test requirements
pip install -r test_requirements.txt
```
