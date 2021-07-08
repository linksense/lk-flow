#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/6/28 16:15
# Copyright 2021 LinkSense Technology CO,. Ltd
import pytest

from lk_flow.config import conf
from lk_flow.core import Context, setup_mod
from lk_flow.models.tasks import Task
from lk_flow.plugin.sql_orm import SQLOrmMod


class TestTrigger:
    mod: SQLOrmMod

    @classmethod
    def setup_class(cls):
        cls.context = Context(config=conf)
        cls.context.config.mod_config["HttpControlServer"] = {"enable": False}
        setup_mod(cls.context)
        cls.mod: SQLOrmMod = cls.context.get_mod(SQLOrmMod.__name__)

    def test_save_task(self):
        make_echo_task = Task(
            name="make_echo_task", command='echo "`date`"', directory="."
        )
        self.mod.delete_task_orm(make_echo_task)
        self.mod.create_task_orm(make_echo_task)

        with pytest.raises(ValueError):
            self.mod.create_task_orm(make_echo_task)
        self.mod.delete_task_orm(make_echo_task)
