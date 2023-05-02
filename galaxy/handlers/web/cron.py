#!/usr/bin/env python3

import config
from galaxy.handlers.web import WebHandler
from galaxy.models.pinnable import Website
from galaxy.tasks.pinnable import check_website


class CronHandler(WebHandler):
    def get(self):
        if "User-Agent" in self.request.headers:
            ua = self.request.headers["User-Agent"]
            if ua != config.cron_user_agent:
                self.set_status(403)
                self.finish()
                return
        websites = self.session.query(Website).all()
        for website in websites:
            self.q.enqueue(check_website, website.id)


cron_handlers = [(r"/_cron/?$", CronHandler)]
