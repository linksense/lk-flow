#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:12
# Copyright 2021 LinkSense Technology CO,. Ltd
import logging
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, List

from lk_flow.env import logger
from lk_flow.utils import time_consuming_log


class EVENT(Enum):
    # 系统初始化
    SYSTEM_SETUP = "system_setup"
    # # 系统启动事件
    # SYSTEM_START = "system_start"
    # 心跳 刷新用
    HEARTBEAT = "heartbeat"
    # 系统致循环结束
    SYSTEM_CLOSE = "system_close"
    # 系统关闭
    SYSTEM_TEARDOWN = "system_teardown"

    # Task
    TASK_PRE_START = "task_pre_start"
    TASK_RUNNING = "task_running"
    TASK_FINISH = "task_finish"
    TASK_RUNNING_ERROR = "task_running_error"  # running 时报错

    TASK_FINISH_ERROR = "task_finish_error"  # TASK_AFTER_FINISH 的钩子事件导致的报错


class Event(object):
    def __init__(self, event_type: EVENT, **kwargs: Any):
        self.__dict__: Dict[str:Any] = kwargs
        self.event_type = event_type

    def __repr__(self) -> str:
        _attr = ", ".join(
            "{}={}".format(k, repr(v))
            for k, v in self.__dict__.items()
            if k != "event_type"
        )
        return f"Event({self.event_type}, {_attr})"

    def __getattribute__(self, *args, **kwargs) -> Any:  # for typing check
        return super(Event, self).__getattribute__(*args, **kwargs)


class EventBus(object):
    def __init__(self):
        self._listeners: Dict[EVENT, List[Callable]] = defaultdict(list)

    def add_listener(self, event_type: EVENT, listener: Callable) -> None:
        self._listeners[event_type].append(listener)

    def publish_event(self, event: Event) -> None:
        logger.debug(f"Get {event}")
        for listener in self._listeners[event.event_type]:
            if logger.level == logging.DEBUG:
                listener = time_consuming_log(logging.DEBUG)(listener)
            # 如果返回 True ，那么消息不再传递下去
            if listener(event):
                break
