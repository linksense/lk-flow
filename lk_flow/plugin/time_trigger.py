#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
import datetime
from typing import Any, Dict

from croniter import croniter

from lk_flow.core import EVENT, Context, Event, ModAbstraction
from lk_flow.models.tasks import Task


class TimeTrigger(ModAbstraction):
    PROCESS_SCHEDULE: Dict[str, datetime.datetime] = {}  # 进程时间表
    context: Context

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        # register event listener
        cls.context = Context.get_instance()
        # add event listener
        cls.context.event_bus.add_listener(EVENT.SYSTEM_SETUP, cls.init_time_trigger)
        cls.context.event_bus.add_listener(EVENT.HEARTBEAT, cls.work)

    @classmethod
    def teardown_mod(cls) -> None:
        pass

    @classmethod
    def work(cls, event: Event) -> None:
        """检查进程是否在运行"""
        for task_name, next_datetime in cls.PROCESS_SCHEDULE.items():
            # 在运行的跳过
            if cls.context.is_running(task_name):
                continue
            process_manager = cls.context.PROCESS_ALL[task_name]
            # 未运行的判断是否运行
            if cls._should_start(event.now, task_name):
                cls.context.run(task_name)
                cls.PROCESS_SCHEDULE[task_name] = croniter(
                    process_manager.config.cron_expression
                ).next(datetime.datetime)

    @classmethod
    def add_task(cls, task: Task) -> None:
        """添加任务到系统"""
        if task.cron_expression:  # 定时启动
            cls.PROCESS_SCHEDULE[task.name] = croniter(task.cron_expression).next(
                datetime.datetime
            )

    @classmethod
    def init_time_trigger(cls, _: Event) -> None:
        """
        初始化时间触发器mod
        通过context里已加载的task进行配置
        需要在SYSTEM_SETUP事件以后进行 （）
        """
        tasks = [i.task for i in cls.context.PROCESS_ALL]
        for task in tasks:
            cls.add_task(task)

    @classmethod
    def _should_start(cls, now: datetime.datetime, task_name: str) -> bool:
        """判断任务是否需要开始"""
        if now >= cls.PROCESS_SCHEDULE[task_name]:
            return True
        return False
