#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/1 14:26
# Copyright 2021 LinkSense Technology CO,. Ltd
import datetime
from typing import Dict, Optional

from pydantic import BaseModel

from lk_flow.models import Task


class SubProcessModel(BaseModel):
    name: str
    config: Task
    pid: Optional[int] = None  # Subprocess pid; None when not running
    state: Optional[str] = None  # process state
    exit_code: Optional[int] = None
    stdout_logfile: Optional[str] = None
    stderr_logfile: Optional[str] = None

    last_start_datetime: Optional[datetime.datetime] = None
    last_stop_datetime: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True


class CommonResponse(BaseModel):
    message: str = "ok"
    code: int = 0
    data: str = None


class ProcessResponse(CommonResponse):
    data: Optional[SubProcessModel] = None


class ProcessMapResponse(CommonResponse):
    data: Optional[Dict[str, SubProcessModel]] = None


class SaveToSqlRequest(BaseModel):
    force: bool = True


class SaveToYamlRequest(BaseModel):
    force: bool = True
    file_path: str = "./yaml"
