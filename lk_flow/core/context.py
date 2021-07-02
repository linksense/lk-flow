#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 16:38
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, ItemsView, Optional, Type

from lk_flow.config import Config
from lk_flow.core.event import EVENT, Event, EventBus
from lk_flow.env import logger
from lk_flow.errors import DuplicateModError
from lk_flow.models import SubProcess, Task

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from lk_flow.core import ModAbstraction


class Context:
    _env: Context = None

    def __init__(self, config: Config):
        Context._env = self
        self.loop_enable: bool = True
        self.config: Config = config
        self.event_bus: EventBus = EventBus()
        self.sleep_time: int = config.sleep_time
        # Process 集合
        self._PROCESS_ALL = {}  # 所有Task
        self._PROCESS_RUNNING = {}  # 正在跑的
        self._PROCESS_STOPPED = {}  # 未激活 or 已结束的
        self._mod_map: Dict[str, Type["ModAbstraction"]] = {}
        # add add_listener
        self.event_bus.add_listener(EVENT.SYSTEM_CLOSE, self.close_loop)
        self.event_bus.add_listener(EVENT.HEARTBEAT, self.state_check)

    @classmethod
    def get_instance(cls) -> Context:
        """
        返回已经创建的 Context 对象

        >>> Context.get_instance()
        Traceback (most recent call last):
            ...
        RuntimeError: Context has not been created. Please Use `Context.get_instance()` after lk_flow init
        """
        if cls._env is None:
            raise RuntimeError(
                "Context has not been created. Please Use `Context.get_instance()` after lk_flow init"
            )
        return cls._env

    # Mod

    def get_mod_map(self) -> ItemsView[str, Type["ModAbstraction"]]:
        return self._mod_map.items()

    def add_mod_map(self, mod_name: str, mod: Type["ModAbstraction"]) -> None:
        if mod_name in self._mod_map.keys():
            _message = (
                f"DuplicateModError at name = {mod_name}, {self._mod_map[mod_name]}"
            )
            raise DuplicateModError(_message)
        self._mod_map[mod_name] = mod

    def get_mod(self, mod_name: str) -> Type["ModAbstraction"]:
        return self._mod_map[mod_name]

    # Process

    def get_process(self, task_name: str) -> SubProcess:
        return self._PROCESS_ALL[task_name]

    # Process Set

    def get_all_processes(self) -> ItemsView[str, SubProcess]:
        return self._PROCESS_ALL.items()

    def get_stopped_processes(self) -> ItemsView[str, SubProcess]:
        return self._PROCESS_STOPPED.items()

    def get_running_processes(self) -> ItemsView[str, SubProcess]:
        return self._PROCESS_RUNNING.items()

    # Task

    def start_task(self, task_name: str) -> None:
        if task_name in self._PROCESS_RUNNING:
            return
        # get subprocess
        process_manager: SubProcess = self._PROCESS_STOPPED.pop(task_name)
        # pre start
        self.event_bus.publish_event(Event(EVENT.TASK_PRE_START, task_name=task_name))
        # start
        asyncio.get_event_loop().run_until_complete(process_manager.start())
        # running
        event = Event(
            EVENT.TASK_RUNNING,
            task_name=task_name,
            task=process_manager.config,
            process=process_manager,
        )
        self.event_bus.publish_event(event)

    def stop_task(self, task_name: str) -> None:
        """停止进程"""
        if task_name not in self._PROCESS_RUNNING:
            return
        process_manager: SubProcess = self._PROCESS_RUNNING.pop(task_name)
        # stop
        asyncio.get_event_loop().run_until_complete(process_manager.stop())
        # running
        event = Event(
            EVENT.TASK_STOP,
            task_name=task_name,
            task=process_manager.config,
            process=process_manager,
        )
        self.event_bus.publish_event(event)

    def add_task(self, task: Task) -> Optional[SubProcess]:
        """添加任务到系统"""
        if task.name in self._PROCESS_ALL:  # 已加载
            logger.warning(f"{task} is already read")
            return
        process_manager = SubProcess(task)
        self._PROCESS_ALL[task.name] = process_manager
        self._PROCESS_STOPPED[task.name] = process_manager

        event = Event(
            EVENT.TASK_ADD, task_name=task.name, task=task, process=process_manager
        )
        self.event_bus.publish_event(event)
        return process_manager

    def delete_task(self, task_name: str) -> None:
        subprocess: SubProcess = self._PROCESS_ALL.pop(task_name, None)
        if subprocess is None:
            return
        if self._PROCESS_RUNNING.pop(task_name, None):
            asyncio.run(subprocess.stop())
        else:
            self._PROCESS_STOPPED.pop(task_name, None)
        event = Event(
            EVENT.TASK_DELETE,
            task_name=task_name,
            task=subprocess.config,
            process=subprocess,
        )
        self.event_bus.publish_event(event)

    # System

    def close_loop(self, event: Event) -> Optional[True]:
        """关闭循环"""
        self.loop_enable = False
        for task_name in self._PROCESS_RUNNING.keys():
            self.stop_task(task_name)
        logger.info(f"Get {event}, close loop.")

    def is_running(self, task_name: str) -> bool:
        """check is running"""
        if task_name in self._PROCESS_RUNNING:
            return True
        return False

    def state_check(self, _: Event) -> None:
        """
        检查进程状态
        进程正常退出则发送 TASK_FINISH事件
        异常退出发送 TASK_RUNNING_ERROR事件
        """
        for name, subprocess in self._PROCESS_RUNNING.copy():
            if subprocess.exit_code is None:
                # still running
                continue
            self._PROCESS_RUNNING.pop(name)
            self._PROCESS_STOPPED[name] = subprocess
