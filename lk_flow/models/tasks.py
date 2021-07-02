#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/16 17:02
# Copyright 2021 LinkSense Technology CO,. Ltd
from typing import Any

from pydantic import BaseModel


class Task(BaseModel):
    name: str
    command: str = None
    directory: str = None
    auto_restart: bool = False
    restart_retries: int = 0
    environment: str = None

    cron_expression: str = None  # None 表示不定时
    trigger_events: str = None  # None 表示无钩子事件

    extra_json: str = "{}"  # 额外字段用于mod扩展

    class Config:
        orm_mode = True

    def __init__(self, **data: Any):
        super().__init__(**data)
