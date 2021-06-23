#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 17:02
# Copyright 2021 LinkSense Technology CO,. Ltd
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String

from lk_flow.env import OrmBaseModel


class Task(BaseModel):
    name: str
    command: str = None
    directory: str = None
    auto_restart: bool = False
    restart_retries: int = 0
    environment: str = None
    cron_expression: str = None  # None 表示不定时

    trigger_events: str = None

    class Config:
        orm_mode = True

    def __init__(self, **data: Any):
        super().__init__(**data)


class TaskOrm(OrmBaseModel):
    __tablename__ = "task"
    task_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(), index=True, nullable=False, unique=True)
    command = Column(String())
    directory = Column(String())
    auto_restart = Column(Boolean, default=False, nullable=False)
    restart_retries = Column(Integer, default=0, nullable=False)
    environment = Column(String())
    cron_expression = Column(String())  # None 表示不定时
