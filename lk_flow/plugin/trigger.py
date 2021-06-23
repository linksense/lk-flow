#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
import datetime
from typing import Dict

from croniter import croniter

from lk_flow.core import Context, EVENT, Event, ModAbstraction
from lk_flow.env import logger, sql_db
from lk_flow.models.subprocess import SubProcess
from lk_flow.models.tasks import Task, TaskOrm


class TimeTrigger(ModAbstraction):
    PROCESS_SCHEDULE: Dict[str, datetime.datetime] = {}  # 进程时间表
    context: Context

    @classmethod
    def setup_mod(cls) -> None:
        cls.context = Context.get_instance()

        cls.context.event_bus.add_listener(EVENT.SYSTEM_SETUP, cls.init_time_trigger)
        cls.context.event_bus.add_listener(EVENT.HEARTBEAT, cls.work)

    @classmethod
    def teardown_mod(cls) -> None:
        pass

    @classmethod
    def work(cls, _: Event) -> None:
        """检查进程是否在运行"""
        for name, next_datetime in cls.PROCESS_SCHEDULE.items():
            # 在运行的跳过
            if cls.context.is_running(name):
                continue
            process_manager = cls.context.PROCESS_ALL[name]
            # 未运行的判断是否运行
            if cls.should_start(name):
                cls.context.run(name)
                cls.PROCESS_SCHEDULE[name] = croniter(
                    process_manager.config.cron_expression
                ).next(datetime.datetime)

    @classmethod
    def init_time_trigger(cls, _: Event) -> None:
        task_orm = sql_db.session.query(TaskOrm).all()
        tasks = [Task.from_orm(_task) for _task in task_orm]
        for task in tasks:
            if task in cls.context.PROCESS_ALL:  # 已由未做完的插件功能帮忙加载
                logger.warning(f"{task} is already read")
                continue
            process_manager = SubProcess(task)
            cls.context.PROCESS_ALL[task.name] = process_manager
            cls.context.PROCESS_SLEEPING[task.name] = process_manager

            if task.cron_expression:  # 定时启动
                cls.PROCESS_SCHEDULE[task.name] = croniter(task.cron_expression).next(
                    datetime.datetime
                )

    @classmethod
    def should_start(cls, task_name: str) -> bool:
        if datetime.datetime.now() >= cls.PROCESS_SCHEDULE[task_name]:
            return True
        return False
