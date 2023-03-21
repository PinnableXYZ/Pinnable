#!/usr/bin/env python3

import calendar
import datetime
import re

import tornado.web
from tornado_sqlalchemy import SessionMixin

import config
from galaxy.handlers.pinnable import PinnableMixin


class BaseHandler(tornado.web.RequestHandler, SessionMixin, PinnableMixin):
    def now(self):
        return int(calendar.timegm(datetime.datetime.utcnow().timetuple()))

    @property
    def mc(self):
        return self.application.mc
    
    @property
    def r(self):
        return self.application.r

    @property
    def env(self):
        return self.application.env

    @property
    def markers(self):
        if not hasattr(self, "_markers"):
            self._markers = []
        return self._markers

    def set_marker(self, name):
        marker = {}
        marker["name"] = name
        marker["latency"] = int(self.request.request_time() * 1000.0)
        self.markers.append(marker)

    @property
    def is_mobile(self):
        ua = None
        if "User-Agent" in self.request.headers:
            ua = self.request.headers["User-Agent"]
        if ua:
            if re.search(
                "iPod|iPhone|Android|Opera Mini|BlackBerry|"
                "webOS|UCWEB|Blazer|PSP|IEMobile|Silk|BB10|Symb",
                ua,
            ):
                return True
            else:
                return False
        else:
            return False

    @property
    def values(self):
        if not hasattr(self, "_values"):
            self._values = {}
            self._values["static_url"] = self.static_url
            self._values["avatar_server_prefix"] = config.avatar_server_prefix
        return self._values
