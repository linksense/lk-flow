#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/17 14:30
# Copyright 2021 LinkSense Technology CO,. Ltd
from lk_flow.env import logger


class LkFlowBaseError(Exception):
    """flow base error 作为所有flow_error的基类"""

    def __init__(self, message: str):
        logger.error(message)
        self.message = message


class RunError(LkFlowBaseError):
    """启动时报错"""


class DictionaryNotExist(LkFlowBaseError):
    """文件夹不存在"""


class ModNotFoundError(RunError):
    """Mod没有找到"""


class RunningError(LkFlowBaseError):
    """运行错误"""


class ProcessRuntimeError(LkFlowBaseError):
    """子进程运行错误"""


class DuplicateModError(LkFlowBaseError, KeyError):
    """mod名称重复"""


class DirNotFoundError(LkFlowBaseError, FileNotFoundError):
    """文件夹未找到"""


class YamlFileExistsError(LkFlowBaseError, FileExistsError):
    """文件已存在"""


class DuplicateTaskNameError(LkFlowBaseError, KeyError):
    """mod名称重复"""
