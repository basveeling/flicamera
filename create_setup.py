#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-18
# @Filename: create_setup.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# This is a temporary solution for the fact that pip install . fails with
# poetry when there is no setup.py and an extension needs to be compiled.
# See https://github.com/python-poetry/poetry/issues/1516. Running this
# script creates a setup.py filled out with information generated by
# poetry when parsing the pyproject.toml.

import os

try:
    from poetry.masonry.builders.sdist import SdistBuilder
    from poetry.factory import Factory
except (ImportError, ModuleNotFoundError) as ee:
    raise ImportError('install poetry by doing pip install poetry to use '
                      f'this script: {ee}')


# Generate a Poetry object that knows about the metadata in pyproject.toml
factory = Factory()
poetry = factory.create_poetry(os.path.dirname(__file__))

# Use the SdistBuilder to genrate a blob for setup.py
sdist_builder = SdistBuilder(poetry, None, None)
setuppy_blob = sdist_builder.build_setup()

if os.path.exists('setup.py'):
    raise FileExistsError('setup.py already exists. Not overwriting it.')

with open('setup.py', 'wb') as unit:
    unit.write(setuppy_blob)
    unit.write(b'\n# This setup.py was autogenerated using poetry.\n')
