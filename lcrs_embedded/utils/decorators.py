import logging
import shlex
import subprocess

from functools import wraps
from .job import Job


logger = logging.getLogger(__name__)


def threaded_api_request(JobType=Job):
    """
    Spawns a new thread and adds another job ID to the queue,
    """

    def outer_wrapper(method):

        @wraps(method)
        def wrapper(instance, *args, **kwargs):
            """
            :param: instance: JSONRequestHandler instance
            """
            job_id = instance.scheduler.add_job(JobType)
            instance.respond_job_id(job_id)
            return method(instance, *args, **kwargs)

        return wrapper

    return outer_wrapper


def thread_safe_method(lock_attr):

    def outer_wrapper(method):

        @wraps(method)
        def wrapper(instance, *args, **kwargs):
            lock = getattr(instance, lock_attr)
            lock.acquire()
            return_value = method(instance, *args, **kwargs)
            lock.release()
            return return_value
        return wrapper

    return outer_wrapper


def run_command_with_timeout(command, timeout=1):
    """
    Runs a command, calling the decorated function with the results of the
    command.
    """

    def outer_rapper(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                p = subprocess.run(
                    *shlex.split(command),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    check=True,
                )
                stdout = p.stdout.decode('utf-8')
                stderr = p.stderr.decode('utf-8')
                succeeded = p.returncode == 0

            except subprocess.TimeoutExpired:
                stdout = ""
                stderr = ""
                succeeded = False
                logger.error("Command timed out: {}".format(command))

            return func(
                *args,
                stdout=stdout,
                stderr=stderr,
                succeeded=succeeded,
                **kwargs
            )

        return wrapper

    return outer_rapper
