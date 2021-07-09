#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/24 16:38
# Copyright 2021 LinkSense Technology CO,. Ltd
from __future__ import annotations

import asyncio
import datetime
import traceback
from typing import TYPE_CHECKING, Dict, ItemsView, Optional, Type

from lk_flow.config import Config
from lk_flow.core.event import EVENT, Event, EventBus
from lk_flow.env import logger
from lk_flow.errors import (
    DuplicateModError,
    DuplicateTaskNameError,
    LkFlowBaseError,
    ModNotFoundError,
    TaskNotFoundError,
)
from lk_flow.models import SubProcess, Task

if TYPE_CHECKING:  # pragma: no cover
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
        self.event_bus.add_listener(EVENT.EXEC_SYSTEM_CLOSE, self._close_loop)
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

    def add_mod(self, mod_name: str, mod: Type["ModAbstraction"]) -> None:
        if mod_name in self._mod_map.keys():
            _message = (
                f"DuplicateModError at name = {mod_name}, {self._mod_map[mod_name]}"
            )
            raise DuplicateModError(_message)
        self._mod_map[mod_name] = mod

    def get_mod(self, mod_name: str) -> Type[Type["ModAbstraction"]]:
        if mod_name not in self._mod_map.keys():
            raise ModNotFoundError(f"{mod_name} not found")
        return self._mod_map[mod_name]

    # Process

    def get_process(self, task_name: str) -> SubProcess:
        if task_name not in self._PROCESS_ALL:
            raise TaskNotFoundError(f"Task {task_name} not found")
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
        self._PROCESS_RUNNING[task_name] = process_manager
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
        self._PROCESS_STOPPED[task_name] = process_manager
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
            message = f"{task.name} is already used. {task}"
            raise DuplicateTaskNameError(message)

        logger.debug(f"add task: {task}")
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

    def _close_loop(self, event: Event) -> Optional[True]:
        """关闭循环"""
        self.loop_enable = False
        for task_name in self._PROCESS_RUNNING.copy().keys():
            self.stop_task(task_name)
        logger.info(f"Get {event}, close loop.")
        self.event_bus.publish_event(Event(EVENT.SYSTEM_CLOSE))

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
        for name, subprocess in self._PROCESS_RUNNING.copy().items():
            if subprocess.exit_code is None:
                # still running
                continue
            self._PROCESS_RUNNING.pop(name)
            self._PROCESS_STOPPED[name] = subprocess

    async def entry_loop(self) -> None:
        while self.loop_enable:
            try:
                self.event_bus.publish_event(
                    Event(EVENT.HEARTBEAT, now=datetime.datetime.now())
                )
            except LkFlowBaseError as err:
                logger.error(err.message)
                logger.error(traceback.format_exc())
            await asyncio.sleep(self.sleep_time)
        return
