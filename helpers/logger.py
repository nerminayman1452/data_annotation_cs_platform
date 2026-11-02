import logging


def trace_warning_logs(e):
    """Create a custom logger with the core Django logging
    
    Parameters
    ----------
    name : str, optional
        the name of module executing this script, default the current existing logger module
    """
    logger = logging.getLogger(__name__)
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    return logger.warning(str({
                'type': type(e).__name__,
                'message': str(e),
                'trace': trace
            }))
