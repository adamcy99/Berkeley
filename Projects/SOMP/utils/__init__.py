from functools import wraps
from os import getpid
import threading

#from app import LOG
from ibmdata import LOG
from .bootstrap import *
#from .cache import *
#from .cdf import cdf_plot
from .dash_table import *
#from .data import *
#from .hybrid_wafermap_galleries import hybrid_wafermap_gallery
#from .plots import *
from .tables import *
#from .url import *


def log_runtime(threshold: int = 5, log_start: bool = False, log_args: bool = True):
    """
    decorator which logs how long a function takes to run
    """

    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if log_start:
                LOG.debug(f"({getpid()} {threading.get_ident()}) {func.__module__}.{func.__name__} started")
            start = dt.now()
            result = func(*args, **kwargs)
            time = dt.now() - start
            if time.total_seconds() > threshold:
                argstr = f", args {args} {kwargs}" if log_args else ""
                LOG.warning(
                    f"({getpid()} {threading.get_ident()}) {func.__module__}.{func.__name__} took {time} to run, "
                    f"threshold {threshold}s{argstr}"
                )
            return result

        return inner_wrapper

    return outer_wrapper
