from flask_rq import RQ
from rq.exceptions import DuplicateJobError
from datetime import datetime

rq = RQ()

def enqueue_one(func, *args, **kwargs):
    n = datetime.now()
    job_id = f'{func.__name__}_{n.year}-{n.month}-{n.day}-{n.hour}-{5 * round(n.minute/5)}'
    try:
        return enqueue(func, unique=True, job_id=job_id, *args, **kwargs)
    except DuplicateJobError as e:
        print(f"Duplicate Job {job_id}")
    

def enqueue(func, *args, **kwargs):
    return rq.queue.enqueue(func, *args, **kwargs)

def init_app(app):
    rq.init_app(app)
