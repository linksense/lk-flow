#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 11:05
# Copyright 2021 LinkSense Technology CO,. Ltd
from pydantic import BaseModel

from lk_flow.models.tasks import Task


class Trigger(BaseModel):
    """触发器是任务的控制器"""

    def trigger_task(self, task: Task) -> None:
        """启动触发任务"""
        ...


class TimeTrigger(BaseModel):
    year: int = None
    month: int = None
    day: int = None
    hour: int = None
    minute: int = None
    second: int = None
    weekday: int = None
