#!/usr/bin/python3
# encoding: utf-8

"""
test_lk_flow
----------------------------------

Tests for `lk_flow` module.
"""
import pytest

import lk_flow


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
        pass

    def teardown_method(self):
        pass

    def test_something(self, benchmark):
        assert lk_flow.__version__
        from lk_flow import __main__

        # assert cost time
        benchmark(__main__.version)
        assert benchmark.stats.stats.max < 0.01

    def test_config(self):
        import os

        from lk_flow.config import Config, conf
        from lk_flow.env import app

        # read flask config
        assert app.config["SQLALCHEMY_DATABASE_URI"] == conf.SQLALCHEMY_DATABASE_URI
        # read config.yaml
        file_name = "config.yaml"
        created_config = False
        if not os.path.exists(file_name):
            created_config = True
            open(file_name, "w", encoding="utf8").write("A: a")
        assert Config().LOG_LEVEL == conf.LOG_LEVEL
        if created_config:
            os.remove(file_name)
