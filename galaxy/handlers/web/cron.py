#!/usr/bin/env python3

import config
from galaxy.handlers.web import WebHandler
from galaxy.models.pinnable import Website
from galaxy.tasks.pinnable import check_website, is_backing_off
from galaxy.utils.jobs import has_pending_job, remember_pending_job


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
            # Sites whose check or pin keeps failing are retried twice a day.
            if is_backing_off(website.id):
                continue
            # Cron fires every 2 minutes; when workers fell behind, enqueueing
            # regardless piled up millions of duplicate checks in Redis.
            if has_pending_job(self.r, "cron-check", website.id):
                continue
            job = self.q.enqueue(check_website, website.id)
            remember_pending_job(self.r, "cron-check", website.id, job)


cron_handlers = [(r"/_cron/?$", CronHandler)]
