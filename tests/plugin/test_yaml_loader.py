#!/usr/bin/env python
# encoding: utf-8
# Created by zza on 2021/7/8 16:01
# Copyright 2021 LinkSense Technology CO,. Ltd
import os
import shutil
from pathlib import Path

import pytest

from lk_flow.config import conf
from lk_flow.core import Context
from lk_flow.errors import DirNotFoundError, YamlFileExistsError
from lk_flow.models import Task
from lk_flow.plugin.yaml_loader import YamlLoader
from tests.test_lk_flow import TestLkFlow


class TestYamlLoader(TestLkFlow):
    dir_name = "./tmp_task_yaml_dir"

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.dir_name)

    def test_init_mod(self):
        dir_name = self.dir_name
        YamlLoader.init_mod({"task_yaml_dir": dir_name})
        assert os.path.exists(dir_name)

    def test_dump_to_file(self):
        Context(conf)

        YamlLoader.setup_mod({})
        YamlLoader.setup_mod({"task_yaml_dir": "./not_exist_dir"})
        abc_path = os.path.join(Path(__file__).parent.parent.parent, "yaml")
        YamlLoader.setup_mod({"task_yaml_dir": abc_path})

        task = Task(
            name="t_time_trigger_task",
            command="/usr/bin/date",
            cron_expression="0/1 * * * * * ",
        )
        with pytest.raises(DirNotFoundError):
            YamlLoader.dump_to_file(task, "./not_exist_dir", force=False)
        YamlLoader.dump_to_file(task, self.dir_name, force=False)
        with pytest.raises(YamlFileExistsError):
            YamlLoader.dump_to_file(task, self.dir_name, force=False)
        YamlLoader.dump_to_file(task, self.dir_name, force=True)
