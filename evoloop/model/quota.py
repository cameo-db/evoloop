"""Recognising a refusal by the account's spend or usage limit, and reading when the limit resets.

Such a refusal is not a failed call: asking again cannot help until the limit resets or is raised.
The client pauses every agent call until then (`ModelClient.pause`), and nothing is charged or stored."""
from __future__ import annotations

import datetime
import re
import time
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:   # Python before 3.9: a reset time is read in the machine's own time zone
    ZoneInfo = None

# What a limit refusal says, in the wordings seen so far. A refusal worded otherwise is treated as an
# ordinary failed call, which costs a few requests before the explorer stops asking.
QUOTA_PATTERN = re.compile(r"spend limit|usage limit|usage-credits|credit balance|out of credits|"
                           r"limit resets|billing|quota|hit your [\w -]*limit|limit\W+resets", re.IGNORECASE)
QUOTA_RETRY_SECONDS = 1800.0   # with no reset time in the message: one probing call per half hour

# "resets Nov 2, 4am (America/New_York)", "resets 4:30pm", "resets 1pm (Europe/Paris)"
RESET = re.compile(r"resets\s+(?:(?P<month>[A-Za-z]{3})[a-z]*\s+(?P<day>\d{1,2}),?\s+)?"
                   r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<half>am|pm)(?:\s*\((?P<zone>[^)]+)\))?",
                   re.IGNORECASE)
MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def quota_reset_time(message: str, now: Optional[float] = None) -> Optional[float]:
    """The reset time a limit message names, as a Unix time a minute past it; None when it names none
    or it cannot be read. A time with no date is the next time the clock shows it."""
    found = RESET.search(message)
    if not found:
        return None
    zone = None
    if found["zone"] and ZoneInfo is not None:
        try:
            zone = ZoneInfo(found["zone"])
        except Exception:   # an unknown zone name: read the time in the machine's own zone
            zone = None
    current = datetime.datetime.fromtimestamp(time.time() if now is None else now, zone)
    hour = int(found["hour"]) % 12 + (12 if found["half"].lower() == "pm" else 0)
    try:
        when = current.replace(hour=hour, minute=int(found["minute"] or 0), second=0, microsecond=0)
        if found["month"]:
            when = when.replace(month=MONTHS.index(found["month"].lower()) + 1, day=int(found["day"]))
            if when < current - datetime.timedelta(days=1):
                when = when.replace(year=when.year + 1)    # a date already past is next year's
        elif when <= current:
            when += datetime.timedelta(days=1)
    except ValueError:      # not a month, or not a date or time that exists
        return None
    return when.timestamp() + 60.0
