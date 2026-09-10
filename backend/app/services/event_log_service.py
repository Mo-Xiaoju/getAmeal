"""事件埋点服务：在业务关键节点追加事件日志。

约定：只 `db.session.add(...)`、不 `commit`，交由调用方已有的 `db.session.commit()`
统一提交，保证事件与业务操作处于同一事务（要么都成功、要么都回滚）。
"""
import json

from app.extensions import db
from app.models import EventLog


class EventLogService:
    """事件日志写入。"""

    @staticmethod
    def record(actor, event_type: str, *, target_type: str = None, target_id: int = None,
               school_id: int = None, extra: dict = None) -> None:
        """追加一条事件日志。

        actor: 触发者（User 或 None）；event_type 受控词表见 EventLog 模型 docstring。
        """
        log = EventLog(
            actor_id=actor.id if actor is not None else None,
            actor_role=getattr(actor, 'role', None),
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            school_id=school_id,
            extra=json.dumps(extra, ensure_ascii=False) if extra else None,
        )
        db.session.add(log)
