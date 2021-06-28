#!/usr/bin/python3
# encoding: utf-8

"""
test_lk_flow
----------------------------------

Tests for `lk_flow` module.
"""

from typing import Any, Dict

import pytest

import lk_flow
from lk_flow.__main__ import run
from lk_flow.core import EVENT, Context, Event, ModAbstraction


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

        # read config.yaml
        file_name = "config.yaml"
        created_config = False
        if not os.path.exists(file_name):
            created_config = True
            open(file_name, "w", encoding="utf8").write("A: a")
        assert Config().LOG_LEVEL == conf.LOG_LEVEL
        if created_config:
            os.remove(file_name)

    def test_run(self):
        assassins_listened = []

        class Assassins(ModAbstraction):
            @classmethod
            def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
                context = Context.get_instance()
                context.event_bus.add_listener(EVENT.HEARTBEAT, cls.assassins_on_call)

            @classmethod
            def teardown_mod(cls) -> None:
                pass

            @classmethod
            def assassins_on_call(cls, event: Event):
                context = Context.get_instance()
                assassins_listened.append(event)
                if len(assassins_listened) > 2:
                    context.event_bus.publish_event(Event(EVENT.SYSTEM_CLOSE))
                    return True

        run()
        assert len(assassins_listened) > 2

    def test_catch_error(self):
        class Terrorists(ModAbstraction):
            @classmethod
            def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
                context = Context.get_instance()
                context.event_bus.add_listener(EVENT.HEARTBEAT, cls.run)

            @classmethod
            def teardown_mod(cls) -> None:
                pass

            @classmethod
            def run(cls, event):
                raise RuntimeError("Explosions are art")

        run()
        del Terrorists
        import gc

        gc.collect()
