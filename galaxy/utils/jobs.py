from rq.exceptions import NoSuchJobError
from rq.job import Job, JobStatus

import config

PENDING_JOB_TTL = 24 * 60 * 60
PENDING_STATUSES = (
    JobStatus.QUEUED,
    JobStatus.STARTED,
    JobStatus.DEFERRED,
    JobStatus.SCHEDULED,
)


def pending_job_key(kind: str, website_id: int) -> str:
    return f"{config.cache_prefix}:{kind}-job:{website_id}"


def has_pending_job(r, kind: str, website_id: int) -> bool:
    """Whether the last `kind` job remembered for this website hasn't finished."""
    job_id = r.get(pending_job_key(kind, website_id))
    if job_id is None:
        return False
    try:
        status = Job.fetch(job_id.decode(), connection=r).get_status()
    except NoSuchJobError:
        return False
    return status in PENDING_STATUSES


def remember_pending_job(r, kind: str, website_id: int, job: Job) -> None:
    r.set(pending_job_key(kind, website_id), job.id, ex=PENDING_JOB_TTL)
