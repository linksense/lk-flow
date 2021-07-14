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
        cls.context.event_bus.add_listener(EVENT.HEARTBEAT, cls._work)

        cls._init_time_trigger()
        cls.context.event_bus.add_listener(EVENT.TASK_ADD, cls._add_task_event_listener)
        cls.context.event_bus.add_listener(
            EVENT.TASK_DELETE, cls._delete_task_event_listener
        )

    @classmethod
    def _work(cls, event: Event) -> None:
        """
        检查进程是否应该运行

        Args:
            event:  Event(EVENT.HEARTBEAT, now=datetime.datetime(2021, 7, 8, 14, 44, 21, 268526))

        Returns:
            None
        """
        for task_name, next_datetime in cls.PROCESS_SCHEDULE.items():
            # 在运行的跳过
            if cls.context.is_running(task_name):
                continue
            process_manager = cls.context.get_process(task_name)
            # 未运行的判断是否运行
            if cls._should_start(event.now, task_name):
                cls.context.start_task(task_name)
                cls.PROCESS_SCHEDULE[task_name] = croniter(
                    process_manager.config.cron_expression
                ).next(datetime.datetime)

    @classmethod
    def _delete_task_event_listener(cls, event: Event) -> None:
        cls.PROCESS_SCHEDULE.pop(event.task_name, None)

    @classmethod
    def _add_task_event_listener(cls, event: Event) -> None:
        """
        TASK_ADD监听
        含有cron_expression属性的task增加值检查表

        Args:
            event:
                Event(
                    EVENT.TASK_ADD,
                    task_name='t_time_trigger',
                    task=Task(
                        name='t_time_trigger',
                        cron_expression='0/1 0 0 * * * '),
                    process=...
                )

        Returns:
            None
        """
        task: Task = event.task
        cls._add_task(task)

    @classmethod
    def _add_task(cls, task: Task) -> None:
        """
        添加任务到系统
        使用TASK_ADD事件触发
        """
        if task.cron_expression:  # 定时启动
            next_datetime = croniter(
                task.cron_expression, datetime.datetime.now()
            ).next(datetime.datetime)
            cls.PROCESS_SCHEDULE[task.name] = next_datetime

    @classmethod
    def _init_time_trigger(cls) -> None:
        """
        初始化时间触发器mod
        通过context里已加载的task进行配置
        """
        tasks = [i.config for _, i in cls.context.get_all_processes()]
        for task in tasks:
            cls._add_task(task)

    @classmethod
    def _should_start(cls, now: datetime.datetime, task_name: str) -> bool:
        """判断任务是否需要开始"""
        if now >= cls.PROCESS_SCHEDULE[task_name]:
            return True
        return False
