#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 14:40
# Copyright 2021 LinkSense Technology CO,. Ltd
import os
import shutil
from typing import Any, Dict

import pytest

from lk_flow.config import conf
from lk_flow.core import Context
from lk_flow.core.mod import (
    ModAbstraction,
    _sub_class_map,
    loading_plugin,
    loading_plugin_command,
    mod_init,
    setup_mod,
    teardown_mod,
)
from lk_flow.plugin import yaml_loader


class TestMod:
    mod_map = dict()
    context: Context

    @classmethod
    def setup_class(cls):
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

        from lk_flow.core.mod import _sub_class_map

        _sub_class_map.update(cls.mod_map)

    def setup_method(self):
        Context._env = None
        self.context = Context(config=conf)
        self.context.config.mod_config["ModC"] = {"enable": False}

    @pytest.mark.asyncio
    async def test_setup_and_teardown_mod(self, capsys):
        loading_plugin(None)
        mod_init(self.context)
        Context._env = None
        self.context = Context(config=conf)
        setup_mod(self.context)
        out, err = capsys.readouterr()
        assert "setup_mod ModB" in out

        teardown_mod(self.context)
        out, err = capsys.readouterr()
        assert "teardown_mod ModB" in out

    def test_init(self, capsys):
        mod_init(self.context)
        out, err = capsys.readouterr()
        assert "init_mod ModA" in out

    def test_loading_plugin_command(self):
        loading_plugin_command()

    def test_mod_dir(self):
        if os.path.exists("./tmp_mod_dir"):
            shutil.rmtree("./tmp_mod_dir")
        os.mkdir("./tmp_mod_dir")
        with pytest.raises(KeyError):
            conf.mod_loaded = False
            loading_plugin(os.path.dirname(yaml_loader.__file__))
        shutil.rmtree("./tmp_mod_dir")
        _sub_class_map.clear()
