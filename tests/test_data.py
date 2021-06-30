#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/28 16:15
# Copyright 2021 LinkSense Technology CO,. Ltd
import pytest

from lk_flow.config import conf
from lk_flow.core import Context, setup_mod
from lk_flow.models.tasks import Task
from lk_flow.plugin.task_sql_orm import TaskSQLOrmMod


class TestTrigger:
    mod: TaskSQLOrmMod

    @classmethod
    def setup_class(cls):
        cls.context = Context(config=conf)
        setup_mod(cls.context)
        cls.mod: TaskSQLOrmMod = cls.context.mod_map["TaskSQLOrmMod"]

    def test_save_task(self):
        make_echo_task = Task(
            name="make_echo_task", command='echo "`date`"', directory="."
        )
        self.mod.delete_task_orm(make_echo_task)
        self.mod.create_task_orm(make_echo_task)

        with pytest.raises(ValueError):
            self.mod.create_task_orm(make_echo_task)
        self.mod.delete_task_orm(make_echo_task)
