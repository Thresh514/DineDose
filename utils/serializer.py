from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, date, time as dt_time

def serialize_for_json(obj):
    """
    Recursively convert dataclass/date/time/list/dict to JSON-serializable structure.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dt_time):
        return obj.isoformat()

    if is_dataclass(obj):
        return {k: serialize_for_json(v) for k, v in asdict(obj).items()}

    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(v) for v in obj]

    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}

    return obj


def row_to_dict(cur, row) -> dict:
    """Convert tuple row to dict without using DictCursor."""
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))

