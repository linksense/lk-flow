#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/28 16:15
# Copyright 2021 LinkSense Technology CO,. Ltd
from lk_flow.models.tasks import Task
from lk_flow.plugin.task_sql_orm import TaskOrm


class TesTTrigger:
    @classmethod
    def setup_class(cls):
        http_server_task = Task(
            name="t_http_server", command="python -m http.server 22", directory="."
        )
        make_echo_task = Task(
            name="make_echo_task", command='echo "`date`"', directory="."
        )

        http_server_orm = TaskOrm(**http_server_task.dict())
