#!/usr/bin/env python3

# Project Ivalice

import os.path

import pylibmc
import redis
import tornado.ioloop
import tornado.locks
import tornado.web
from jinja2 import Environment, PackageLoader
from loguru import logger
from tornado.options import define, options
from tornado_sqlalchemy import SQLAlchemy

import config
from galaxy.handlers.web.system import System404Handler
from galaxy.utils.filters import format_bytes, format_tokens

define("port", default=12345, help="run on the given port", type=int)


def build_handlers():
    from galaxy.handlers.web.api import api_handlers
    from galaxy.handlers.web.cron import cron_handlers
    from galaxy.handlers.web.dl import dl_handlers
    from galaxy.handlers.web.pinnable import pinnable_handlers
    from galaxy.handlers.web.profile import profile_handlers
    from galaxy.handlers.web.system import system_handlers

    return (
        pinnable_handlers
        + profile_handlers
        + cron_handlers
        + system_handlers
        + dl_handlers
        + api_handlers
        + [(r"/(.*)$", System404Handler)]
    )


class Application(tornado.web.Application):
    def __init__(self):
        handlers = build_handlers()
        settings = {
            "db": SQLAlchemy(config.database_url),
            "site_title": "Pinnable",
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "xsrf_cookies": True,
            "cookie_secret": config.cookie_secret,
            "login_url": "/auth/signin",
            "debug": config.ivalice_debug,
        }
        super().__init__(handlers, **settings)
        self.env = Environment(
            loader=PackageLoader("galaxy", "templates"),
            extensions=["jinja2.ext.i18n"],
            autoescape=True,
        )
        self.env.filters["format_bytes"] = format_bytes
        self.env.filters["format_tokens"] = format_tokens
        self.mc = pylibmc.Client(
            [config.memcached_host],
            binary=True,
            behaviors={"tcp_nodelay": True, "ketama": True},
        )
        self.r = redis.Redis(host=config.redis_host, port=config.redis_port, db=0)


async def main():
    tornado.options.parse_command_line()

    app = Application()
    app.listen(options.port)
    logger.info("Listening on port {port}", port=options.port)

    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


def dev():
    tornado.ioloop.IOLoop.current().run_sync(main)


if __name__ == "__main__":
    dev()
