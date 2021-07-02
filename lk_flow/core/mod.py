#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 11:17
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import abc
import importlib.util
import inspect
import logging
import os
from typing import Any, Callable, Dict, Optional, Type

from lk_flow.config import conf
from lk_flow.core import Context
from lk_flow.env import logger
from lk_flow.utils import time_consuming_log

_sub_class_map: Dict[str, Type[ModAbstraction]] = {}


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
    def get_commands(cls, mod_config: Dict[str, Any]) -> Dict[str, Callable]:
        """增加系统默认命令"""


@time_consuming_log(logging.INFO)
def mod_init(context: Context) -> None:
    """init mod"""
    for name, mod in _sub_class_map.items():
        mod_config: dict = context.config.mod_config[name]
        if not mod_config.get("enable", True):
            logger.info(f"[{name} mod] not enabled. pass.")
            continue
        context.add_mod_map(name, mod)
        logger.info(f"[{name} mod] init start")
        mod.init_mod(mod_config)
        logger.info(f"[{name} mod] init finish")


@time_consuming_log(logging.INFO)
def setup_mod(context: Context) -> None:
    """setup all mod"""
    for name, mod in _sub_class_map.items():
        mod_config: dict = context.config.mod_config[name]
        if not mod_config.get("enable", True):
            logger.info(f"[{name} mod] not enabled. pass.")
            continue
        context.add_mod_map(name, mod)
        logger.info(f"[{name} mod] setup start")
        mod.setup_mod(mod_config)
        logger.info(f"[{name} mod] setup finish")


@time_consuming_log(logging.INFO)
def teardown_mod(context: Context) -> None:
    """teardown all mod"""
    for name, mod in context.get_mod_map():
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
        for _name, _sub_class in mod.__dict__.items():
            if (
                "ModAbstraction" != _name
                and inspect.isclass(_sub_class)
                and issubclass(_sub_class, ModAbstraction)
            ):
                if _name in _sub_class_map.keys():
                    raise KeyError("存在相同名称的Mod")
                _sub_class_map[_name] = _sub_class
        logger.debug(f"Loading plugin {_file}")


def _loading_sys_plugin() -> None:
    """载入系统mod"""
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../plugin"))
    _loading_plugin(dir_path)


def loading_plugin(mod_dir: Optional[str]) -> None:
    """通过config.mod_dir载入mod"""
    if conf.mod_loaded:
        logger.info("mod is already loaded. pass")
        return

    _loading_sys_plugin()
    if mod_dir:
        logger.info(f"Loading {mod_dir} mods")
        _loading_plugin(mod_dir)
    else:
        logger.debug(f"mod_dir = {mod_dir}, pass loading user plugin")
    conf.mod_loaded = True
    return


def loading_plugin_command() -> Dict[str, Callable]:
    loading_plugin(conf.mod_dir)
    command_map = dict()
    for name, mod in _sub_class_map.items():
        mod_config: dict = conf.mod_config[name]
        if not mod_config.get("enable", True):
            logger.debug(f"[{name} mod] not enabled. pass.")
            continue
        mod_command_map: Dict[str, Callable] = mod.get_commands(mod_config)
        if mod_command_map:
            logger.debug(f"[{name} mod] loading commands {mod_command_map.keys}")
            command_map.update(mod_command_map)

    conf.mod_loaded = True
    return command_map
