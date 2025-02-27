#!/usr/bin/env python3

from tornado.web import authenticated

from galaxy.handlers.web import WebHandler
from galaxy.tasks.pinnable import check_account


class ProfileHandler(WebHandler):
    @authenticated
    def get(self):
        self.q.enqueue(check_account, self.current_user.id)
        self.finalize("profile/profile.html")


profile_handlers = [(r"/profile/?$", ProfileHandler)]
