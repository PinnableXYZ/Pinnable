#!/usr/bin/env python3

from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

import config
from galaxy.handlers.web import WebHandler
from galaxy.models.pinnable import Website
from galaxy.tasks.pinnable import check_website, has_recent_pin_failure

CRON_CHECK_JOB_TTL = 24 * 60 * 60


def cron_check_job_key(website_id: int) -> str:
    return f"{config.cache_prefix}:cron-check-job:{website_id}"


def has_pending_check(r, website_id: int) -> bool:
    """Whether cron's last check job for this website is still queued or running."""
    job_id = r.get(cron_check_job_key(website_id))
    if job_id is None:
        return False
    try:
        status = Job.fetch(job_id.decode(), connection=r).get_status()
    except NoSuchJobError:
        return False
    return status in (JobStatus.QUEUED, JobStatus.STARTED)


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
            if has_recent_pin_failure(website.id):
                continue
            # Cron fires every 2 minutes; when workers fell behind, enqueueing
            # regardless piled up millions of duplicate checks in Redis.
            if has_pending_check(self.r, website.id):
                continue
            job = self.q.enqueue(check_website, website.id)
            self.r.set(cron_check_job_key(website.id), job.id, ex=CRON_CHECK_JOB_TTL)


cron_handlers = [(r"/_cron/?$", CronHandler)]
