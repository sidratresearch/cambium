import logging

root_logger_name = "CambiumLogger"


def init_logging() -> logging.Logger:
    """Function to call once, returns the top-level Cambium logger

    Module-specific loggers are children of this logger
    """
    root_logger = logging.getLogger(root_logger_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    return root_logger


def get_logger(module_name: str) -> logging.Logger:
    """Get a module-specific logger"""
    return logging.getLogger(f"{root_logger_name}.{module_name}")
