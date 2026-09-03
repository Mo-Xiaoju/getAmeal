"""圈子（QQ/微信群）相关路由。"""
from flask import Blueprint, g, request

from app.services.circle_service import CircleService
from app.services.message_service import MessageService
from app.utils.decorators import optional_login, require_consumer, require_login
from app.utils.exceptions import ValidationError
from app.utils.responses import ok

bp_circle = Blueprint('circle', __name__)


@bp_circle.route('', methods=['GET'], strict_slashes=False)
@optional_login
def list_circles():
    """按学校浏览圈子（school_id 必填，带登录态时回显 joined）。"""
    params = request.args.to_dict()
    return ok(CircleService.list(params))


@bp_circle.route('', methods=['POST'], strict_slashes=False)
@require_consumer
def create_circle():
    """创建圈子（需学生/管理员，商户不可；创建者自动成为成员）。"""
    data = request.get_json(silent=True) or {}
    return ok(CircleService.create(g.current_user, data), message='创建成功')


@bp_circle.route('/joined', methods=['GET'])
@require_login
def list_joined_circles():
    """我加入的圈子（分页）。"""
    params = request.args.to_dict()
    return ok(CircleService.joined(g.current_user, params))


@bp_circle.route('/<int:circle_id>', methods=['GET'])
@optional_login
def get_circle_detail(circle_id):
    """圈子详情（带登录态时回显 joined）。"""
    return ok(CircleService.get_detail(circle_id))


@bp_circle.route('/<int:circle_id>', methods=['PUT'])
@require_consumer
def update_circle(circle_id):
    """更新自己的圈子（仅创建者）。"""
    data = request.get_json(silent=True) or {}
    return ok(CircleService.update(g.current_user, circle_id, data), message='更新成功')


@bp_circle.route('/<int:circle_id>', methods=['DELETE'])
@require_consumer
def delete_circle(circle_id):
    """解散自己的圈子（软删除，仅创建者）。"""
    CircleService.delete(g.current_user, circle_id)
    return ok(None, message='解散成功')


@bp_circle.route('/<int:circle_id>/join', methods=['POST'])
@require_consumer
def toggle_join_circle(circle_id):
    """加入/退出圈子（幂等，仅限本校同学）。"""
    return ok(CircleService.toggle_join(g.current_user, circle_id))


@bp_circle.route('/<int:circle_id>/members', methods=['GET'])
@require_login
def get_circle_members(circle_id):
    """圈子成员列表（分页）。"""
    params = request.args.to_dict()
    return ok(CircleService.members(circle_id, params))


@bp_circle.route('/<int:circle_id>/messages', methods=['GET'])
@require_login
def get_circle_messages(circle_id):
    """圈子群聊历史（仅成员可见，before_id 向上拉取）。"""
    params = request.args.to_dict()
    return ok(CircleService.list_messages(circle_id, g.current_user, params))


@bp_circle.route('/<int:circle_id>/messages', methods=['POST'])
@require_consumer
def send_circle_message(circle_id):
    """发送圈内群聊消息（仅成员，商户不可；socket 断开时的 REST 兜底）。"""
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        raise ValidationError(message='消息内容不能为空', code=4000)
    channel = {'type': 'circle', 'id': circle_id}
    message = MessageService.send(g.current_user, channel, content)
    return ok(message, message='发送成功')
