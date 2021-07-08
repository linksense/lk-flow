#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 16:28
# Copyright 2021 LinkSense Technology CO,. Ltd

from typing import Any, Dict

from lk_flow.__main__ import run
from lk_flow.config import conf
from lk_flow.core import EVENT, Context, Event, ModAbstraction


class TestContext:
    @classmethod
    def setup_class(cls):
        conf.mod_config["HttpControlServer"] = {"enable": False}

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
                    context.event_bus.publish_event(Event(EVENT.EXEC_SYSTEM_CLOSE))
                    return True

        from lk_flow.core.mod import _sub_class_map

        _sub_class_map[Assassins.__name__] = Assassins
        run()
        assert len(assassins_listened) > 2

        del _sub_class_map[Assassins.__name__]

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

        from lk_flow.core.mod import _sub_class_map

        _sub_class_map[Terrorists.__name__] = Terrorists
        run()
        del _sub_class_map[Terrorists.__name__]
        del Terrorists
        import gc

        gc.collect()
