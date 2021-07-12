#!/usr/bin/python3
# encoding: utf-8
"""
A better experience in PyCharm:

Settings - Tools - Python integrated Tools - Testing - Default test runner: 'pytest'
"""

import os

import pytest


def setup_module(module):
    """setup any state specific to the execution of the given module."""
    from lk_flow.__main__ import generate_config

    generate_config()


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method."""
    pass


if __name__ == "__main__":
    pytest.main(["-s", "--doctest-modules", os.path.dirname(os.path.dirname(__file__))])
