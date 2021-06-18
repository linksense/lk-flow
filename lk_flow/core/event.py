#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:12
# Copyright 2021 LinkSense Technology CO,. Ltd
from collections import defaultdict
from enum import Enum
from typing import Callable


class EVENT(Enum):
    # 系统初始化后触发
    # post_system_init()
    POST_SYSTEM_INIT = "post_system_init"

    # Task
    TASK_READY = "task_ready"
    TASK_PRE_START = "task_pre_start"
    TASK_RUNNING = "task_running"
    TASK_FINISH = "task_finish"
    TASK_AFTER_FINISH = "task_after_finish"
    TASK_RUNNING_ERROR = "task_running_error"  # running 时报错
    TASK_FINISH_ERROR = "task_finish_error"  # TASK_AFTER_FINISH 的钩子事件导致的报错


class Event(object):
    def __init__(self, event_type: EVENT, **kwargs):
        self.__dict__ = kwargs
        self.event_type = event_type

    def __repr__(self) -> str:
        return " ".join("{}:{}".format(k, v) for k, v in self.__dict__.items())


class EventBus(object):
    def __init__(self):
        self._listeners = defaultdict(list)

    def add_listener(self, event_type: EVENT, listener: Callable) -> None:
        self._listeners[event_type].append(listener)

    def publish_event(self, event: EVENT) -> None:
        for listener in self._listeners[event.event_type]:
            # 如果返回 True ，那么消息不再传递下去
            if listener(event):
                break
