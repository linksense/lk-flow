# lk-flow

--- 

Life process manager

## 安装

```bash
pip install lk_flow
```

## 启动

```bash

# 启动服务
lk_flow generate_config # 生成配置文件
lk_flow init # 初始化
lk_flow run # 启动服务


# 查看帮助
lk_flow -- --help

# 查看命令帮助
lk_flow create --help

# 查看服状态
lk_flow status

# 创建task
lk_flow create

# 查看task时间表
lk_flow schedule

```

* [Black formatter](https://github.com/psf/black)

> This project use black, please set `Continuation indent` = 4  
> Pycharm - File - Settings - Editor - Code Style - Python - Tabs and Indents

* [Flake8 lint](https://github.com/PyCQA/flake8)

> Use flake8 to check your code style.

## Features

---

* api控制
* 命令控制
* 生命周期管理
* 统计信息展示
* 进程状态控制
* hook
* 支持事件驱动
