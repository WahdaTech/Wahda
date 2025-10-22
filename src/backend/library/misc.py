import asyncio
import re

from core import tp


async def forever() -> tp.TExc:
    await asyncio.Future()

    return None


def telegram_escape_markdown(msg: str) -> str:
    chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(chars)}])", r"\\\1", msg)
