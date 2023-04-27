#!/usr/bin/env python3

import time
from datetime import datetime

from siwe import SiweMessage

from galaxy.handlers.web import WebHandler


class SystemAuthHandler(WebHandler):
    def get(self):
        self.values["theme_color"] = "#ffcc33"
        self.finalize("system/auth.html")

    def post(self):
        message = None
        if "message" in self.request.arguments:
            message = self.get_argument("message")
        signature = None
        if "signature" in self.request.arguments:
            signature = self.get_argument("signature")
        if message and signature:
            message = message.replace("\r\n", "\n")
            message = message.replace("\r", "\n")
            self.set_header("Content-Type", "text/plain")
            try:
                siwe_message: SiweMessage = SiweMessage(message=message)
                siwe_message.verify(signature)
            except:
                self.values["error"] = "Authentication failed"
            if hasattr(siwe_message, "expiration_time"):
                expiration = siwe_message.expiration_time
                dt = datetime.strptime(expiration, "%Y-%m-%dT%H:%M:%S.%fZ")
                unix_timestamp = int(time.mktime(dt.timetuple()))
            else:
                unix_timestamp = self.now() + (86400 * 7)
            cookie_content = (
                "pinnable:" + siwe_message.address + ":" + str(unix_timestamp)
            )
            self.set_secure_cookie("pinnable", cookie_content, expires_days=7)
            self.redirect("/")


class SystemHomeHandler(WebHandler):
    def get(self):
        # self.values["theme_color"] = "#ffd659"
        self.values["theme_color"] = "#ffcc33"
        self.finalize("system/home.html")


class SystemPricingHandler(WebHandler):
    def get(self):
        # self.values["theme_color"] = "#a3b18a"
        self.values["theme_color"] = "#a0bd6c"
        self.finalize("system/pricing.html")


class SystemPlanetHandler(WebHandler):
    def get(self):
        # self.values["theme_color"] = "#c0c0c0"
        self.values["theme_color"] = "#c5c5c5"
        self.finalize("system/planet.html")


class SystemSignOutHandler(WebHandler):
    def post(self):
        self.clear_cookie("pinnable")
        self.redirect("/")


class System404Handler(WebHandler):
    def get(self, path):
        self.set_status(404)
        self.finalize("system/404.html")


system_handlers = [
    (r"/", SystemHomeHandler),
    (r"/auth/?$", SystemAuthHandler),
    (r"/signout/?$", SystemSignOutHandler),
    (r"/pricing/?$", SystemPricingHandler),
    (r"/planet/?$", SystemPlanetHandler),
]
