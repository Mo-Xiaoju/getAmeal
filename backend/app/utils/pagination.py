"""分页参数解析与分页结果构造工具。"""
import math

from flask import current_app, request


def parse_pagination(page_size_max: int = 50) -> dict:
    """从请求参数解析分页信息。

    支持查询参数：page（页码，从 1 起）、page_size（每页条数）。
    返回 { page, page_size, offset }。
    """
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.args.get('page_size', current_app.config.get('PAGE_SIZE_DEFAULT', 10)))
    except (TypeError, ValueError):
        page_size = current_app.config.get('PAGE_SIZE_DEFAULT', 10)

    page = max(page, 1)
    page_size = min(max(page_size, 1), page_size_max)

    return {'page': page, 'page_size': page_size, 'offset': (page - 1) * page_size}


def paginate(query, page: int, page_size: int) -> dict:
    """对 SQLAlchemy Query 分页并构造统一分页结果。

    返回 { items, total, page, page_size, total_pages }。
    """
    total = query.count()
    total_pages = math.ceil(total / page_size) if total else 0
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }
