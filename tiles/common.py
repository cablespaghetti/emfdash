from datetime import datetime

ORDINALS = {1: "st", 2: "nd", 3: "rd", 21: "st", 22: "nd", 23: "rd", 31: "st"}


def format_day(d: datetime) -> str:
    suffix = ORDINALS.get(d.day, "th")
    return f"{d.strftime('%A')} {d.day}{suffix}"
