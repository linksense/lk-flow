#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 14:40
# Copyright 2021 LinkSense Technology CO,. Ltd
import gc
import os.path
from typing import Any, Dict

import pytest

from lk_flow.config import conf
from lk_flow.core import Context
from lk_flow.core.mod import (
    ModAbstraction,
    loading_plugin,
    mod_init,
    setup_mod,
    teardown_mod,
)


class TestMod:
    mod_map = dict()
    context: Context

    @classmethod
    def setup_class(cls):
        cls.context = Context(config=conf)
        cls.context.config.mod_config["ModC"] = {"enable": False}

        class ModA(ModAbstraction):
            @classmethod
            def init_mod(cls, mod_config: Dict[str, Any]) -> None:
                print("init_mod", cls.__name__)

            @classmethod
            def setup_mod(cls, mod_config: Dict[str, Any]):
                print("setup_mod", cls.__name__)

            @classmethod
            def teardown_mod(cls):
                print("teardown_mod", cls.__name__)

        class ModB(ModAbstraction):
            @classmethod
            def setup_mod(cls, mod_config: Dict[str, Any]):
                print("setup_mod", cls.__name__)

            @classmethod
            def teardown_mod(cls):
                print("teardown_mod", cls.__name__)

        class ModC(ModB):
            @classmethod
            def teardown_mod(cls):
                print("teardown_mod", cls.__name__)

        cls.mod_map = {
            "ModA": ModA,
            "ModB": ModB,
            "ModC": ModC,
        }

    def test_setup_mod(self, capsys):
        setup_mod(self.context)
        out, err = capsys.readouterr()
        assert "setup_mod ModB" in out

    def test_teardown_mod(self, capsys):
        teardown_mod(self.context)
        out, err = capsys.readouterr()
        assert "teardown_mod ModB" in out

    def test_error_name(self, capsys):
        class ModB(self.mod_map["ModA"]):
            """A mistake produces The baby Class"""

        with pytest.raises(KeyError):
            setup_mod(self.context)

        del ModB
        gc.collect()

        setup_mod(self.context)

        out, err = capsys.readouterr()
        assert "setup_mod ModB" in out

    def test_init(self, capsys):
        mod_init(self.context)
        out, err = capsys.readouterr()
        assert "init_mod ModA" in out

    def test_loading_plugin(self):
        from lk_flow.plugin import trigger

        mod_dir = os.path.dirname(trigger.__file__)
        loading_plugin(mod_dir)
