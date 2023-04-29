#!/usr/bin/env python3

import calendar
import datetime
import re

import tornado.web
from rq import Queue
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
    def q(self):
        if not hasattr(self, "_q"):
            self._q = Queue("pinnable", connection=self.r, default_timeout=1800)
        return self._q

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

    def get_current_user(self):
        cookie = self.get_secure_cookie("pinnable")
        if cookie:
            cookie = cookie.decode("utf-8")
            cookie = cookie.split(":")
            if len(cookie) == 3:
                if cookie[0] == "pinnable":
                    address = cookie[1]
                    expiration = int(cookie[2])
                    if expiration > self.now():
                        account = self.get_account(address)
                        if account:
                            return account
                        else:
                            account = self.create_account(address)
                            return account
        return None

    def add_error(self, problem: str):
        self.values["errors"] += 1
        if problem is not None:
            self.values["error_messages"].append(problem)

    def ok(self):
        return self.values["errors"] == 0

    @property
    def values(self):
        if not hasattr(self, "_values"):
            self._values = {}
            self._values["pinnable_api_prefix"] = config.pinnable_api_prefix
            self._values["str"] = str
            self._values["breadcrumb"] = self.breadcrumb
            self._values["static_url"] = self.static_url
            self._values["xsrf_form_html"] = self.xsrf_form_html
            self._values["account"] = self.current_user
            self._values["errors"] = 0
            self._values["error_messages"] = []
            self._values["request"] = self.request
        return self._values

    def on_finish(self):
        self.session.close()
