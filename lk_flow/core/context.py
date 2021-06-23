#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 16:38
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import asyncio
from typing import ClassVar, Dict, Optional

from lk_flow.config import Config
from lk_flow.core.event import EVENT, Event, EventBus
from lk_flow.env import logger
from lk_flow.models.subprocess import SubProcess


class Context:
    _env: Context = None
    # Process 集合
    PROCESS_ALL = {}  # 所有Task
    PROCESS_RUNNING = {}  # 正在跑的
    PROCESS_STOPPED = {}  # 已结束的
    PROCESS_SLEEPING = {}  # 未激活的

    def __init__(self, config: Config):
        Context._env = self
        self.loop_enable: bool = True
        self.config: Config = config
        self.event_bus: EventBus = EventBus()
        self.event_bus.add_listener(EVENT.SYSTEM_CLOSE, self.close_loop)
        self.event_bus.add_listener(EVENT.HEARTBEAT, self.state_check)
        self.sleep_time: int = config.sleep_time
        self.mod_map: Dict[str, ClassVar] = {}

    @classmethod
    def get_instance(cls) -> Context:
        """
        返回已经创建的 Context 对象
        """
        if cls._env is None:
            raise RuntimeError(
                "Context has not been created. Please Use `Context.get_instance()` after RQAlpha init"
            )
        return cls._env

    def close_loop(self, event: Event) -> Optional[True]:
        """关闭循环"""
        self.loop_enable = False
        logger.info(f"Get {event}, close loop.")

    def is_running(self, task_name: str) -> bool:
        if task_name in self.PROCESS_RUNNING:
            return True
        return False

    def run(self, task_name: str) -> None:
        if task_name in self.PROCESS_RUNNING:
            return
        # get subprocess
        process_manager: SubProcess = self.PROCESS_SLEEPING.pop(
            task_name, None
        ) or self.PROCESS_STOPPED.pop(task_name)
        # pre start
        self.event_bus.publish_event(Event(EVENT.TASK_PRE_START))
        # start
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_manager.start())
        # running
        self.event_bus.publish_event(Event(EVENT.TASK_RUNNING))

    def state_check(self, _: Event) -> None:
        """
        检查进程状态
        进程正常退出则发送 TASK_FINISH事件
        异常退出发送 TASK_RUNNING_ERROR事件
        """
        for name, subprocess in self.PROCESS_RUNNING.copy():
            if subprocess.exit_code is None:
                # still running
                continue
            self.PROCESS_RUNNING.pop(name)
            self.PROCESS_STOPPED[name] = subprocess
            if subprocess.exit_code == 0:
                # normal exit
                self.event_bus.publish_event(Event(EVENT.TASK_FINISH))
            else:  # raise error
                self.event_bus.publish_event(Event(EVENT.TASK_RUNNING_ERROR))
