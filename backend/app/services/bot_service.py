"""官方消息机器人：账号标识与自动回复规则。

机器人是一个普通用户账号（role='student'），靠保留用户名识别。
刻意不引入新的 role 取值：role 只在注册白名单（schemas/auth.py:ROLES）、
管理员角色校验（admin_service.ADMIN_ROLES）和管理端下拉框三处被枚举，
新取值会波及管理端且没有收益。账号由 `flask seed-bot` 创建，密码为随机串，
因此不可被登录。
"""
from typing import Optional

from app.models import Message, User

#: 机器人账号的保留用户名 / 昵称（seed-bot 建号与识别逻辑共用）
BOT_USERNAME = 'xiaoxiaozhushou'
BOT_NICKNAME = '小助手'

_WELCOME = (
    '你好，我是校园美食小助手～\n'
    '想找人聊天可以试试：\n'
    '· 在笔记、评论、圈子成员里点任意头像，进对方主页后点「发私信」\n'
    '· 私信页左下角有「推荐联系人」，直接点开就能聊\n'
    '回复关键词（如「私信」「关注」「收藏」）我也会告诉你具体位置。'
)

#: 关键词 → 回复文案；按元组顺序取首个命中的分支，全不命中则用 _FALLBACK
_KEYWORD_REPLIES = (
    (('私信', '聊天', '会话'), '点头像就能进对方主页，主页上有「发私信」按钮；也可以直接在私信页左下角的「推荐联系人」里点我。'),
    (('关注', '粉丝'), '在别人的主页或笔记详情页点「关注」即可。关注之后，对方会出现在你私信页的「推荐联系人」里，方便直接开聊。'),
    (('收藏', '点赞'), '笔记和店铺详情页都有「点赞」「收藏」按钮，收藏过的内容可以在「个人中心 → 我的收藏」里回看。'),
    (('笔记', '发布', '探店'), '在「探店笔记」页点「发布笔记」就能写啦，可以配图并关联一家店铺。'),
    (('店铺', '菜单', '菜品'), '「店铺列表」里可以按学校筛选，进店后能看到菜单和大家的评价。'),
)

_FALLBACK = '收到～这个我还没学会。你可以问我「私信」「关注」「收藏」「发布笔记」「店铺」相关的用法。'


class BotService:
    """官方助手的账号查询与回复生成。"""

    @staticmethod
    def get_bot() -> Optional[User]:
        """按保留用户名取机器人账号；不存在或已停用时返回 None。"""
        return User.query.filter_by(username=BOT_USERNAME, is_active=True).first()

    @staticmethod
    def build_reply(sender: User, recipient: User, text: str) -> Optional[str]:
        """生成机器人回复；收件人不是机器人时返回 None（调用方据此跳过）。

        调用时机在发信人那条消息落库之后（见 MessageService.send 末尾），
        所以「我发给机器人的消息数 == 1」即表示这是首次接触，回欢迎语。
        """
        if recipient is None or recipient.username != BOT_USERNAME:
            return None

        sent = Message.query.filter_by(user_id=sender.id, recipient_id=recipient.id).count()
        if sent <= 1:
            return _WELCOME

        lowered = (text or '').lower()
        for keywords, reply in _KEYWORD_REPLIES:
            if any(k in lowered for k in keywords):
                return reply
        return _FALLBACK
