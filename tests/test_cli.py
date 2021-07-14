#!/usr/bin/env python
# encoding: utf-8
import os

from fire import testutils

from lk_flow import __main__


class CoreTest(testutils.BaseTestCase):
    def test_version(self):
        with self.assertOutputMatches(stdout=".*"):
            __main__.fire.Fire(__main__.version, command=[])

    def test_version_help_info(self):
        with self.assertRaisesFireExit(0, regexp="显示当前版本"):
            __main__.fire.Fire(
                {"version": __main__.version}, command=["version", "--help"]
            )

    def test_init(self):
        with self.assertRaisesFireExit(0, regexp="初始化系统"):
            __main__.fire.Fire({"init": __main__.init}, command=["init", "--help"])
        __main__.init()

        assert os.path.exists("lk_flow.db")

    def test_generate_config(self):
        with self.assertOutputMatches(".*lk_flow_config.yaml"):
            __main__.fire.Fire(
                {"generate_config": __main__.generate_config},
                command=["generate_config"],
            )
        assert os.path.exists("lk_flow_config.yaml")
