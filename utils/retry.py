import random
import time
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


def run_with_retry(
    operation: Callable[[], T],
    retries: int = 2,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    allowed_exceptions: Iterable[type[BaseException]] = (Exception,),
    logger=None,
) -> T:
    attempt = 0
    while True:
        try:
            return operation()
        except tuple(allowed_exceptions) as exc:
            attempt += 1
            if attempt > retries:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay * (1.0 + random.uniform(-0.1, 0.1))
            if logger:
                logger.warning(
                    "Retrying after error (%s). attempt=%s delay=%.2fs",
                    exc,
                    attempt,
                    delay,
                )
            time.sleep(delay)
