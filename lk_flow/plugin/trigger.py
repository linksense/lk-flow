#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
import datetime
from typing import Any, Dict

from croniter import croniter
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from lk_flow.core import EVENT, Context, Event, ModAbstraction
from lk_flow.env import logger
from lk_flow.models.subprocess import SubProcess
from lk_flow.models.tasks import Task

Model = declarative_base()


class TaskOrm(Model):
    __tablename__ = "task"
    task_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(), index=True, nullable=False, unique=True)
    command = Column(String())
    directory = Column(String())
    auto_restart = Column(Boolean, default=False, nullable=False)
    restart_retries = Column(Integer, default=0, nullable=False)
    environment = Column(String())
    cron_expression = Column(String())  # None 表示不定时


class TimeTrigger(ModAbstraction):
    PROCESS_SCHEDULE: Dict[str, datetime.datetime] = {}  # 进程时间表
    context: Context
    engine: Engine
    db_session: sessionmaker

    @classmethod
    def init_mod(cls, mod_config: Dict[str, Any]) -> None:
        engine = create_engine(
            mod_config["SQLALCHEMY_DATABASE_URI"], convert_unicode=True
        )
        Model.metadata.create_all(bind=engine)

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        if "SQLALCHEMY_DATABASE_URI" not in mod_config:
            logger.info(
                f"No config 'SQLALCHEMY_DATABASE_URI' in mod_config['{cls.__name__}']"
            )
            return
        cls.engine = create_engine(
            mod_config["SQLALCHEMY_DATABASE_URI"], convert_unicode=True
        )

        cls.db_session = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

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
        for name, next_datetime in cls.PROCESS_SCHEDULE.items():
            # 在运行的跳过
            if cls.context.is_running(name):
                continue
            process_manager = cls.context.PROCESS_ALL[name]
            # 未运行的判断是否运行
            if cls.should_start(event.now, name):
                cls.context.run(name)
                cls.PROCESS_SCHEDULE[name] = croniter(
                    process_manager.config.cron_expression
                ).next(datetime.datetime)

    @classmethod
    def init_time_trigger(cls, _: Event) -> None:
        if not TaskOrm.__table__.exists(cls.engine):
            raise RuntimeError("请先初始化 lk_flow init")
        session = cls.db_session()
        task_orm = session.query(TaskOrm).all()
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

        session.close()

    @classmethod
    def should_start(cls, now: datetime.datetime, task_name: str) -> bool:
        if now >= cls.PROCESS_SCHEDULE[task_name]:
            return True
        return False
