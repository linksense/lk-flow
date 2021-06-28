#!/usr/bin/python3
# encoding: utf-8
import logging

import sentry_sdk
from flask import Flask

from lk_flow.config import conf

if conf.sentry_dns:  # pragma: no cover
    sentry_sdk.init(dsn=conf.sentry_dns, traces_sample_rate=1.0)


def init_log(log: logging.Logger) -> logging.Logger:
    log.setLevel(conf.LOG_LEVEL)
    if conf.LOG_FORMAT:
        logging.basicConfig(format=conf.LOG_FORMAT)
    return log


logger = logging.getLogger("lk_flow")
init_log(logger)
del init_log

app = Flask(__name__)
app.config.from_object(conf)
