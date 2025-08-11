from loguru import logger

# -------------------------------------------------------
# LOGGER_INIT_OK - custom init OK loguru function
# -------------------------------------------------------
def logger_init_ok(status: str) -> None:
    return logger.opt(colors=True).info(f"[  <bold><green>OK</green></bold>  ] {status}")
