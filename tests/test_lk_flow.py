#!/usr/bin/python3
# encoding: utf-8

"""
test_lk_flow
----------------------------------

Tests for `lk_flow` module.
"""

import pytest

import lk_flow
from lk_flow import Context


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get("https://github.com/audreyr/cookiecutter-pypackage")


class TestLkFlow:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self):
        del Context._env
        Context._env = None

    def teardown_method(self):
        pass

    def test_something(self, benchmark):
        assert lk_flow.__version__
        from lk_flow import __main__

        # assert cost time
        benchmark(__main__.version)
        assert benchmark.stats.stats.max < 0.01
