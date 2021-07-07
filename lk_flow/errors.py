#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/17 14:30
# Copyright 2021 LinkSense Technology CO,. Ltd
from lk_flow.env import logger


class _BaseError(Exception):
    """flow base error 作为所有flow_error的基类"""

    def __init__(self, message: str):
        logger.error(message)
        self.message = message


class RunError(_BaseError):
    """启动时报错"""


class DictionaryNotExist(_BaseError):
    """文件夹不存在"""


class ModNotFoundError(RunError):
    """Mod没有找到"""


class RunningError(_BaseError):
    """运行错误"""


class ProcessRuntimeError(_BaseError):
    """子进程运行错误"""


class DuplicateModError(_BaseError, KeyError):
    """mod名称重复"""


class DuplicateTaskNameError(_BaseError, KeyError):
    """mod名称重复"""
