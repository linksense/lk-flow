#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 16:28
# Copyright 2021 LinkSense Technology CO,. Ltd
import shutil
from typing import Any, Dict

import pytest

from lk_flow import Task, logger
from lk_flow.__main__ import run
from lk_flow.config import conf
from lk_flow.core import EVENT, Context, Event, ModAbstraction
from lk_flow.errors import DuplicateModError, LkFlowBaseError, ModNotFoundError


class TestContext:
    @classmethod
    def setup_class(cls):
        conf.mod_config["HttpControlServer"] = {"enable": False}
        logger.setLevel("DEBUG")

    @classmethod
    def teardown_class(cls):
        conf.mod_config["HttpControlServer"] = {}

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
                if len(assassins_listened) == 1:
                    context.start_task("t_http_server")
                    context.add_task(Task(name="t_watch_date", command="watch date"))
                    context.start_task("t_watch_date")

                if len(assassins_listened) == 2:
                    context.delete_task("t_http_server")
                    # not error
                    context.delete_task("t_http_server")
                    context.get_stopped_processes()
                    context.get_running_processes()
                    with pytest.raises(DuplicateModError):
                        context.add_mod(Assassins.__name__, Assassins)
                    with pytest.raises(ModNotFoundError):
                        context.get_mod("ModNotFoundError")
                    raise LkFlowBaseError("a test error")
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

    def test_config(self):
        import os

        from lk_flow import Config, conf

        # read config.yaml
        file_name = "config.yaml"
        created_config = False
        if not os.path.exists(file_name):
            created_config = True
            open(file_name, "w", encoding="utf8").write("A: a")
        assert Config().log_save_dir == conf.log_save_dir
        if created_config:
            os.remove(file_name)

    def test_log_dir(self):
        from lk_flow.main import _make_sys_log_file

        shutil.rmtree(conf.log_save_dir)
        _make_sys_log_file()
