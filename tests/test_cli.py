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
        if os.path.exists("/usr/bin/lk_flow"):
            os.remove("/usr/bin/lk_flow")
        __main__.init()

        assert os.path.exists("lk_flow.db")

    def test_generate_config(self):
        with self.assertOutputMatches(".*lk_flow_config.yaml"):
            __main__.fire.Fire(
                {"generate_config": __main__.generate_config},
                command=["generate_config"],
            )
        assert os.path.exists("lk_flow_config.yaml")
        __main__.generate_config(force=True)

    def test_convert_to_yaml(self):
        from lk_flow.core.mod import loading_plugin_command

        current_directory = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        command_map = {
            "version": __main__.version,
            "run": __main__.run,
            "init": __main__.init,
            "generate_config": __main__.generate_config,
        }
        command_map.update(loading_plugin_command())
        __main__.fire.Fire(command_map, command=["convert_config_to_yaml"])
        assert os.path.exists("lk_user_http.yaml")
        assert os.path.exists("lk_user_admin.yaml")
        assert os.path.exists("lk_user_grpc.yaml")
        __main__.fire.Fire(command_map, command=["convert_config_to_yaml"])
        os.remove("lk_user_http.yaml")
        os.remove("lk_user_admin.yaml")
        os.remove("lk_user_grpc.yaml")
        os.chdir(current_directory)
