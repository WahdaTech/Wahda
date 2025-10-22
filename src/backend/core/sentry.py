__all__ = ["capture_exception"]

import os

from sentry_sdk import capture_exception, init

from . import telemetry

LOG = telemetry.get_logger()


SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
RELEASE = os.environ.get("RELEASE", "unknown")

if SENTRY_DSN is not None:
    init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        release=RELEASE,
        # TODO: enable it when we are actually ready to process and realize it.
        enable_tracing=False,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    )
    LOG.info("sentry set for DSN: {dsn}", dsn=SENTRY_DSN)
