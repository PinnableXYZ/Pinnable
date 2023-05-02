#!/usr/bin/env python3

from tornado.web import authenticated

from galaxy.handlers.web import WebHandler


class ProfileHandler(WebHandler):
    @authenticated
    def get(self):
        self.finalize("profile/profile.html")


profile_handlers = [(r"/profile/?$", ProfileHandler)]
