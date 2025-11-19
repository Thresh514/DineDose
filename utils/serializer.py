from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, date, time as dt_time

def serialize_for_json(obj):
    """
    递归把 dataclass / date / time / list / dict 等
    转成可以直接 jsonify 的结构。
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
    """把 tuple row 转成 dict，避免依赖 DictCursor。"""
    columns = [desc[0] for desc in cur.description]
    return dict(zip(columns, row))

