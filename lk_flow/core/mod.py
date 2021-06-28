#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 11:17
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import abc
import importlib.util
import logging
import os
from typing import Any, Dict, Optional, Type

from lk_flow.core import Context
from lk_flow.env import logger
from lk_flow.utils import time_consuming_log


class ModAbstraction:
    @classmethod
    def init_mod(cls, mod_config: Dict[str, Any]) -> None:
        """初始化命令会调用的方法"""
        logger.info(f"[{__name__}] not implemented function init_mod. pass.")

    @classmethod
    @abc.abstractmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        """mod启动时 会执行的函数"""

    @classmethod
    @abc.abstractmethod
    def teardown_mod(cls) -> None:
        """mod关闭时 会执行的函数"""

    @classmethod
    def sub_classes(cls) -> Dict[str, Type[ModAbstraction]]:
        """
        返回所有继承的子类

        遇到继承时，所有子类都会被启动
        """
        subs = {_class.__name__: _class for _class in cls.__subclasses__()}
        for _name, _class in subs.copy().items():
            if sub_subs := _class.sub_classes():
                if subs.keys() & sub_subs.keys():
                    raise KeyError("存在相同名称的Mod")
                subs.update(sub_subs)
        return subs


@time_consuming_log(logging.INFO)
def mod_init(context: Context) -> None:
    """init mod"""
    for name, mod in ModAbstraction.sub_classes().items():
        mod_config: dict = context.config.mod_config[name]
        if not mod_config.get("enable", True):
            logger.info(f"[{name} mod] not enabled. pass.")
            continue
        context.mod_map[name] = mod
        logger.info(f"[{name} mod] init start")
        mod.init_mod(mod_config)
        logger.info(f"[{name} mod] init finish")


@time_consuming_log(logging.INFO)
def setup_mod(context: Context) -> None:
    """setup all mod"""
    for name, mod in ModAbstraction.sub_classes().items():
        mod_config: dict = context.config.mod_config[name]
        if not mod_config.get("enable", True):
            logger.info(f"[{name} mod] not enabled. pass.")
            continue
        context.mod_map[name] = mod
        logger.info(f"[{name} mod] setup start")
        mod.setup_mod(mod_config)
        logger.info(f"[{name} mod] setup finish")


@time_consuming_log(logging.INFO)
def teardown_mod(context: Context) -> None:
    """teardown all mod"""
    for name, mod in context.mod_map.items():
        logger.info(f"[{name} mod] teardown start")
        mod.teardown_mod()
        logger.info(f"[{name} mod] teardown finish")


def _loading_plugin(dir_path: str) -> None:
    """loading mod file by dir_path"""
    for _file in os.listdir(dir_path):
        if not _file.endswith(".py"):
            continue
        spec = importlib.util.spec_from_file_location(
            os.path.basename(_file)[:-3], os.path.join(dir_path, _file)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        logger.info(f"Loading plugin {_file}")


def loading_sys_plugin() -> None:
    """载入系统mod"""
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../plugin"))
    _loading_plugin(dir_path)


def loading_plugin(mod_dir: Optional[str]) -> None:
    """通过config.mod_dir载入mod"""
    if mod_dir:
        logger.info(f"Loading {mod_dir} mods")
        return _loading_plugin(mod_dir)
    else:
        logger.info(f"mod_dir = {mod_dir}, pass")
        return
