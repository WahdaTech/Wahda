__all__ = ["get_logger", "otel_trace", "get_root_tracer"]

import inspect
import logging
import os
import sys

import loguru
import opentelemetry._logs as _otel_logs
import opentelemetry.exporter.otlp.proto.grpc._log_exporter as _otel_otlp_exporter
import opentelemetry.sdk._logs as _otel_sdk_logs
import opentelemetry.sdk._logs.export as _otel_sdk_logs_export
import opentelemetry.sdk.resources as _otel_sdk_resources
import opentelemetry.sdk.trace as _otel_sdk_trace
import opentelemetry.trace as otel_trace


def __get_env(var_name: str, default: str) -> str:
    env_prefix = "WD"
    return os.environ.get(f"{env_prefix}_{var_name}", default)


WD_OTEL_ENABLED = __get_env("OTEL_ENABLED", "0") == "1"
WD_OTEL_SERVICE_NAME = __get_env("OTEL_SERVICE_NAME", "tradelink")
WD_OTEL_OTLP_ENDPOINT = __get_env("OTEL_OTLP_ENDPOINT", "127.0.0.1:4317")
WD_LOGGER_OTEL_HANDLER = __get_env("LOGGER_OTEL_HANDLER", "otlp")
WD_LOGGER_OTEL_LEVEL = __get_env("LOGGER_OTEL_LEVEL", "DEBUG")
WD_LOGGER_CONSOLE_LEVEL = __get_env("LOGGER_CONSOLE_LEVEL", "INFO")
WD_LOGGER_CONSOLE_COLORIZE = __get_env("LOGGER_CONSOLE_COLORIZE", "1") == "1"


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Remove default logger.
loguru.logger.remove()
# Intercept and reroute all default logger logs (from libs, etc.) to loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

_tracer = otel_trace.get_tracer("root_tracer")


def get_logger() -> "loguru.Logger":
    return loguru.logger


def get_root_tracer() -> otel_trace.Tracer:
    return _tracer


# Convert loguru logs to otel compatible form, also inject correlation with trace.
class LoguruLoggingHandler(_otel_sdk_logs.LoggingHandler):
    def emit(self, record: logging.LogRecord) -> None:
        trace_id: int = 0x0
        span_id: int = 0x0
        # Compatibility cast from loguru record to logging record.
        for key, val in record.extra.items():  # type: ignore
            if key == "otel_trace_id" and isinstance(val, int):
                trace_id = val
            elif key == "otel_span_id" and isinstance(val, int):
                span_id = val
            elif isinstance(val, bool | str | bytes | int | float):
                setattr(record, f"extra.{key}", val)
            else:
                setattr(record, f"extra.{key}", str(val))  # type: ignore
        del record.extra  # type: ignore

        if trace_id != 0x0 and span_id != 0x0:
            span_ctx = otel_trace.SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                is_remote=False,
                trace_flags=otel_trace.TraceFlags(0x01),
            )
            ctx = otel_trace.set_span_in_context(otel_trace.NonRecordingSpan(span_ctx))
            tracer = get_root_tracer()
            with tracer.start_as_current_span("log", context=ctx):  # type: ignore
                super().emit(record)
        else:
            super().emit(record)


if WD_OTEL_ENABLED:
    otel_trace.set_tracer_provider(_otel_sdk_trace.TracerProvider())

if WD_OTEL_ENABLED and WD_LOGGER_OTEL_HANDLER in ("console", "otlp"):
    otel_logger_provider = _otel_sdk_logs.LoggerProvider(
        resource=_otel_sdk_resources.Resource.create(
            {
                "service.name": WD_OTEL_SERVICE_NAME,
                "service.instance.id": os.uname().nodename,
            }
        )
    )
    _otel_logs.set_logger_provider(otel_logger_provider)

    match WD_LOGGER_OTEL_HANDLER:
        case "console":
            processor = _otel_sdk_logs_export.BatchLogRecordProcessor(
                _otel_sdk_logs_export.ConsoleLogExporter()
            )

        case "otlp":
            processor = _otel_sdk_logs_export.BatchLogRecordProcessor(
                _otel_otlp_exporter.OTLPLogExporter(
                    endpoint=WD_OTEL_OTLP_ENDPOINT,
                    insecure=True,
                )
            )

    otel_logger_provider.add_log_record_processor(processor)  # type: ignore

    loguru.logger.add(
        LoguruLoggingHandler(logger_provider=otel_logger_provider),
        format="{message}",
        level=WD_LOGGER_OTEL_LEVEL,
        colorize=False,
        diagnose=False,
        backtrace=False,
        enqueue=True,
    )

fmt = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " | <level>{level: <8}</level>"
    " | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
    "\n> <level>{message}</level>"
    "\n> <i><fg 8>{extra}</fg 8></i>"
)
loguru.logger.add(
    sys.stderr,
    format=fmt,
    level=WD_LOGGER_CONSOLE_LEVEL,
    colorize=WD_LOGGER_CONSOLE_COLORIZE,
    diagnose=False,
    backtrace=False,
    enqueue=True,
)
