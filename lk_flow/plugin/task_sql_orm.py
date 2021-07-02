#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/30 11:13
# Copyright 2021 LinkSense Technology CO,. Ltd
from typing import Any, Dict

from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from lk_flow.core import Context, ModAbstraction
from lk_flow.env import logger
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
    trigger_events = Column(String())


class TaskSQLOrmMod(ModAbstraction):
    engine: Engine
    db_session: sessionmaker
    context: Context

    @classmethod
    def init_mod(cls, mod_config: Dict[str, Any]) -> None:
        engine = create_engine(
            mod_config["SQLALCHEMY_DATABASE_URI"], convert_unicode=True
        )
        Model.metadata.create_all(bind=engine)

    @classmethod
    def setup_mod(cls, mod_config: Dict[str, Any]) -> None:
        # 没有配置不会启动mod 但是不会报错
        if "SQLALCHEMY_DATABASE_URI" not in mod_config:
            logger.info(
                f"No config 'SQLALCHEMY_DATABASE_URI' in mod_config['{cls.__name__}']"
            )
            return
        cls.engine = create_engine(
            mod_config["SQLALCHEMY_DATABASE_URI"], convert_unicode=True
        )
        # session_maker
        cls.db_session = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )

        cls.context = Context.get_instance()
        cls.loading_task_from_mysql()

    @classmethod
    def teardown_mod(cls) -> None:
        pass

    @classmethod
    def loading_task_from_mysql(cls) -> None:
        if not TaskOrm.__table__.exists(cls.engine):
            raise RuntimeError("请先初始化 lk_flow init")
        session = cls.db_session()
        task_orm = session.query(TaskOrm).all()
        tasks = [Task.from_orm(_task) for _task in task_orm]
        for task in tasks:
            cls.context.add_task(task)
        session.close()

    @classmethod
    def create_task_orm(cls, task: Task) -> None:
        """将task存储到数据库中"""
        session = cls.db_session()
        if session.query(TaskOrm).filter_by(name=task.name).first():
            session.close()
            raise ValueError(f"Task name is duplicated {task.name}")
        obj = TaskOrm(**task.dict())
        session.add(obj)
        session.commit()
        session.close()

    @classmethod
    def delete_task_orm(cls, task: Task) -> None:
        """从数据库中删除任务"""
        session = cls.db_session()
        obj = session.query(TaskOrm).filter_by(name=task.name).first()
        if not obj:
            return
        session.delete(obj)
        session.commit()
        session.close()
        return
