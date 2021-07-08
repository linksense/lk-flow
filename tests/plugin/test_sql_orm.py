#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/8 17:30
# Copyright 2021 LinkSense Technology CO,. Ltd
import os

import pytest

from lk_flow import Context, Task, conf
from lk_flow.errors import RunError
from lk_flow.plugin.sql_orm import SQLOrmMod
from tests.test_lk_flow import TestLkFlow


class TestSqlOrm(TestLkFlow):
    mod = SQLOrmMod

    def test_setup(self):
        self.mod.setup_mod({})

    def test_loading_task(self):
        Context(conf)
        if os.path.exists("lk_flow.db"):
            os.remove("lk_flow.db")
        open("lk_flow.db", "w", encoding="utf8").write("")
        with pytest.raises(RunError):
            self.mod.setup_mod({"SQLALCHEMY_DATABASE_URI": "sqlite:///lk_flow.db"})

        self.mod.init_mod({"SQLALCHEMY_DATABASE_URI": "sqlite:///lk_flow.db"})
        self.mod.setup_mod({"SQLALCHEMY_DATABASE_URI": "sqlite:///lk_flow.db"})

        make_echo_task = Task(
            name="make_echo_task", command='echo "`date`"', directory="."
        )
        self.mod.delete_task_orm(make_echo_task)
        self.mod.create_task_orm(make_echo_task)
        self.mod.create_task_orm(make_echo_task, force=True)
        self.mod.setup_mod({"SQLALCHEMY_DATABASE_URI": "sqlite:///lk_flow.db"})

        with pytest.raises(ValueError):
            self.mod.create_task_orm(make_echo_task)
        self.mod.delete_task_orm(make_echo_task)
