#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 11:17
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import abc
import logging
from typing import Dict, Type

from lk_flow.core import Context
from lk_flow.env import logger
from lk_flow.utils import time_consuming_log


class ModAbstraction:
    @classmethod
    @abc.abstractmethod
    def setup_mod(cls) -> None:
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
def setup_mod(context: Context) -> None:
    """setup all mod"""
    for name, mod in ModAbstraction.sub_classes().items():
        context.mod_map[name] = mod
        logger.info(f"[{name} mod] setup start")
        mod.setup_mod()
        logger.info(f"[{name} mod] setup finish")


@time_consuming_log(logging.INFO)
def teardown_mod(context: Context) -> None:
    """teardown all mod"""
    for name, mod in context.mod_map.items():
        logger.info(f"[{name} mod] teardown start")
        mod.teardown_mod()
        logger.info(f"[{name} mod] teardown finish")
