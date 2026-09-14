"""E2E smoke test through the Vite dev proxy (http://localhost:5173).

覆盖阶段2 + 店铺模块核心链路：
  选学校 -> 首页推荐 -> 店铺列表(筛选) -> 店铺详情 -> 注册(绑定学校) -> 评价 -> 收藏 -> 改学校
"""
import json
import os
import sys
import urllib.request
import urllib.error

# 脚本位于 backend/tests/ 下，把 backend/ 加入 sys.path，便于末尾直接连库清理测试账号
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = 'http://localhost:5173/api'

results = []


def call(method, path, token=None, payload=None, expect=0, record=True):
    """发一个请求。record=False 用于"前置条件探测"——那种请求的成败不该计入回归结果。"""
    url = BASE + path
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode('utf-8'))
    if record:
        ok = body.get('code') == expect
        results.append((ok, f'{method} {path}', body.get('message')))
    return body.get('data'), body.get('code'), body.get('message')


def check(name, cond):
    results.append((bool(cond), name, '' if cond else 'FAIL'))


# 1. 学校列表
data, code, msg = call('GET', '/schools')
check('schools count>=6', code == 0 and len(data or []) >= 6)
if data:
    s = data[0]
    print('first school:', s['name'], '| shop_count =', s.get('shop_count'))

# 2. 选学校后拉取该校店铺
sid = data[0]['id']
data, code, msg = call('GET', f'/schools/{sid}/shops?page=1&page_size=5')
check('school shops ok', code == 0 and data and data.get('total', 0) >= 1)
print('school shops total:', data and data.get('total'))

# 3. 推荐
data, code, msg = call('GET', f'/shops/recommend?school_id={sid}&page_size=6')
check('recommend ok', code == 0 and len(data.get('items', []) or []) >= 1)
print('recommend count:', len(data.get('items', []) or []))

# 4. 店铺列表：按学校 + 评分排序
data, code, msg = call('GET', f'/shops?school_id={sid}&sort=rating&page=1&page_size=5')
check('shop list sorted', code == 0 and len(data.get('items', []) or []) >= 1)
if data and data.get('items'):
    ratings = [it['avg_rating'] for it in data['items']]
    check('rating desc', ratings == sorted(ratings, reverse=True))

# 5. 店铺详情
shop = data['items'][0]
shop_id = shop['id']
detail, code, msg = call('GET', f'/shops/{shop_id}')
check('shop detail', code == 0 and detail and detail['id'] == shop_id)
print('shop:', detail['name'], '| rating =', detail['avg_rating'], '| count =', detail['rating_count'])
print('  favorited (anon) =', detail.get('favorited'))

# 6. 注册（绑定学校）
import random
rand = random.randint(1000, 9999)
username = f'e2e_{rand}'
reg_data, code, msg = call('POST', '/auth/register',
                           payload={'username': username, 'password': 'pass123456',
                                    'nickname': f'测试{rand}', 'school_id': sid})
check('register ok', code == 0 and reg_data and reg_data.get('access_token'))
token = reg_data['access_token']
user = reg_data['user']
check('register school bound', user.get('school_id') == sid and (user.get('school') or {}).get('id') == sid)
print('registered:', username, '| school =', (user.get('school') or {}).get('name'))

# 7. 发表评价（校验评分后 avg_rating 变化）
detail0 = detail
data, code, msg = call('POST', f'/shops/{shop_id}/reviews',
                       token=token, payload={'rating': 5, 'content': 'E2E自动化评价，很好吃！'})
check('add review', code == 0 and data and data.get('id'))
detail2, code, msg = call('GET', f'/shops/{shop_id}')
check('rating count+1', detail2['rating_count'] == detail0['rating_count'] + 1)
print('avg_rating:', detail0['avg_rating'], '->', detail2['avg_rating'],
      '| count:', detail0['rating_count'], '->', detail2['rating_count'])

# 8. 评价列表含昵称
data, code, msg = call('GET', f'/shops/{shop_id}/reviews?page=1&page_size=10')
check('reviews have nickname', code == 0 and any(r.get('nickname') == f'测试{rand}' for r in data.get('items', [])))

# 9. 收藏 / 取消
data, code, msg = call('POST', f'/shops/{shop_id}/favorite', token=token)
check('favorite on', code == 0 and data and data.get('favorited') is True)
detail3, code, msg = call('GET', f'/shops/{shop_id}', token=token)
check('detail favorited=True', detail3.get('favorited') is True)
data, code, msg = call('DELETE', f'/shops/{shop_id}/favorite', token=token)
check('favorite off', code == 0 and data and data.get('favorited') is False)

# 10. 我的收藏 / 我的评价
data, code, msg = call('GET', '/user/favorites?page=1&page_size=5', token=token)
check('favorites list ok', code == 0)
data, code, msg = call('GET', '/user/reviews?page=1&page_size=5', token=token)
check('my reviews ok', code == 0 and len(data.get('items', [])) >= 1)

# 11. 个人中心改学校（切到第2所学校）
schools_data, code, msg = call('GET', '/schools')
sid2 = schools_data[1]['id']
me, code, msg = call('PUT', '/auth/me', token=token, payload={'school_id': sid2})
check('change school ok', code == 0 and me.get('school_id') == sid2)
print('changed school to:', (me.get('school') or {}).get('name'))

# 12. 评价互动：关联菜品 / 图片 / 回复 / 点赞
data, code, msg = call('GET', '/user/reviews?page=1&page_size=5', token=token)
rid = data['items'][0]['id']

# 关联菜品的评价：店铺均分与菜品均分都要动，菜品页的「菜品评价」里要能查到
dishes, code, msg = call('GET', f'/shops/{shop_id}/dishes?page=1&page_size=5')
dish_items = (dishes or {}).get('items') or []
dish_id = dish_items[0]['id'] if dish_items else None
dish_before = None
linked_rid = None
if dish_id:
    dish_before, code, msg = call('GET', f'/dishes/{dish_id}')
    data, code, msg = call('POST', f'/shops/{shop_id}/reviews', token=token,
                           payload={'rating': 4, 'content': 'E2E 关联菜品的评价',
                                    'images': ['/uploads/e2e-not-a-real-file.png'],
                                    'dish_id': dish_id})
    check('add dish-linked review', code == 0 and data and data.get('dish_id') == dish_id)
    linked_rid = data.get('id') if data else None
    check('review returns images as list',
          data and data.get('images') == ['/uploads/e2e-not-a-real-file.png'])
    dish_after, code, msg = call('GET', f'/dishes/{dish_id}')
    check('dish rating_count+1', dish_after['rating_count'] == dish_before['rating_count'] + 1)
    data, code, msg = call('GET', f'/dishes/{dish_id}/reviews?page=1&page_size=10')
    mine = [r for r in data.get('items', []) if r['id'] == linked_rid]
    check('dish reviews list contains it', code == 0 and len(mine) == 1)
    check('dish review carries dish_name', bool(mine and mine[0].get('dish_name')))
else:
    print('  (本店无菜品，跳过关联菜品的断言)')

# 游客读评价列表：必须 code=0（少了 @optional_login 这里会是 500）且 liked 恒 false
data, code, msg = call('GET', f'/shops/{shop_id}/reviews?page=1&page_size=5')
check('anon reviews ok', code == 0)
check('anon liked all false', all(r.get('liked') is False for r in data.get('items', [])))

# 回复：顶层 + 嵌套（嵌套的要被归一化到根并带出 @对象）
data, code, msg = call('POST', f'/reviews/{rid}/replies', token=token, payload={'content': 'E2E 回复'})
check('add reply', code == 0 and data and data.get('id'))
reply_id = data.get('id') if data else None
check('reply has no @target', data and data.get('reply_to_user_id') is None)
data, code, msg = call('POST', f'/reviews/{rid}/replies', token=token,
                       payload={'content': 'E2E 二级回复', 'parent_id': reply_id})
check('add nested reply', code == 0 and data and data.get('parent_id') == reply_id)
# 被回复人由服务端从父评论作者派生（两边都是本测试账号），客户端从没传过这个字段
check('nested reply derives @target', data and data.get('reply_to_user_id') is not None)
check('nested reply has @nickname', data and data.get('reply_to_nickname') == f'测试{rand}')

data, code, msg = call('GET', f'/shops/{shop_id}/reviews?page=1&page_size=10', token=token)
row = next((r for r in data.get('items', []) if r['id'] == rid), None)
# reply_count 是「根回复 + 子回复」的总数（2），replies 只给根（1 条）
check('review embeds reply preview', row and row.get('reply_count') == 2 and len(row.get('replies') or []) == 1)
check('reply preview nests child', row and len((row.get('replies') or [{}])[0].get('replies') or []) == 1)

data, code, msg = call('GET', f'/reviews/{rid}/replies?page=1&page_size=10', token=token)
check('review replies endpoint', code == 0 and data.get('total') == 1)

# 点赞：同一用户点两次 = 一开一关，列表里的 liked 要跟着变
data, code, msg = call('POST', f'/reviews/{rid}/like', token=token)
check('like review on', code == 0 and data.get('liked') is True and data.get('like_count') == 1)
data, code, msg = call('GET', f'/shops/{shop_id}/reviews?page=1&page_size=10', token=token)
row = next((r for r in data.get('items', []) if r['id'] == rid), None)
check('liked=true when logged in', row and row.get('liked') is True)
data, code, msg = call('POST', f'/reviews/{rid}/like', token=token)
check('like review off', code == 0 and data.get('liked') is False and data.get('like_count') == 0)

# 回复本身也能点赞，走的是 /api/comments/<id>/like（评价回复与笔记评论同一张表）
data, code, msg = call('POST', f'/comments/{reply_id}/like', token=token)
check('like reply on', code == 0 and data.get('liked') is True and data.get('like_count') == 1)
data, code, msg = call('POST', f'/comments/{reply_id}/like', token=token)
check('like reply off', code == 0 and data.get('liked') is False)

# 故意留着一条评价点赞 + 一个回复点赞不撤销：第 13 步删评价时正好验证级联清理
data, code, msg = call('POST', f'/reviews/{rid}/like', token=token)
check('re-like review for purge check', code == 0 and data.get('liked') is True)
data, code, msg = call('POST', f'/comments/{reply_id}/like', token=token)
check('re-like reply for purge check', code == 0 and data.get('liked') is True)

# 商户不可点赞/回复（4031）。演示商户没种子过就跳过，不让这条拦住整个回归
mdata, mcode, mmsg = call('POST', '/auth/login', record=False,
                          payload={'username': 'merchant', 'password': 'demo1234'})
if mcode == 0 and mdata and mdata.get('access_token'):
    mtoken = mdata['access_token']
    _, code, _ = call('POST', f'/reviews/{rid}/like', token=mtoken, expect=4031)
    check('merchant cannot like review', code == 4031)
    _, code, _ = call('POST', f'/reviews/{rid}/replies', token=mtoken,
                      payload={'content': 'x'}, expect=4031)
    check('merchant cannot reply', code == 4031)
else:
    print('  (无演示商户，跳过商户 4031 断言)')

# 13. 删除评价：关联菜品的要回退菜品均分，且回复/点赞一并清掉
if linked_rid:
    data, code, msg = call('DELETE', f'/user/reviews/{linked_rid}', token=token)
    check('delete dish-linked review', code == 0)
    dish_after, code, msg = call('GET', f'/dishes/{dish_id}')
    check('dish rating_count reverted', dish_after['rating_count'] == dish_before['rating_count'])

data, code, msg = call('DELETE', f'/user/reviews/{rid}', token=token)
check('delete review ok', code == 0)
data, code, msg = call('GET', f'/shops/{shop_id}/reviews?page=1&page_size=50')
check('deleted review gone', code == 0 and all(r['id'] != rid for r in data.get('items', [])))

# 14. 清理测试账号
# comments / comment_likes / likes 的 user_id 都是无级联的外键，删用户前必须先清干净，
# 否则 db.session.delete(u) 直接 IntegrityError。
from app import create_app
from app.models import Comment, CommentLike, Like, User
from app.extensions import db

app = create_app('development')
with app.app_context():
    u = User.query.filter_by(username=username).first()
    if u:
        # 级联检查（直连 SQL）：上面删掉那两条评价后，它们的回复与点赞都该没了
        leftovers = Comment.query.filter_by(review_id=rid).count()
        check('review replies purged', leftovers == 0)
        if linked_rid:
            check('dish review replies purged', Comment.query.filter_by(review_id=linked_rid).count() == 0)
        check('review likes purged', Like.query.filter_by(review_id=rid).count() == 0)
        check('comment likes purged', CommentLike.query.filter(CommentLike.user_id == u.id).count() == 0)

        # 评价本身走接口删（要回退均分），这里只兜底清掉没有级联的三个外键引用
        CommentLike.query.filter_by(user_id=u.id).delete(synchronize_session=False)
        Comment.query.filter_by(user_id=u.id).delete(synchronize_session=False)
        Like.query.filter_by(user_id=u.id).delete(synchronize_session=False)
        db.session.delete(u)
        db.session.commit()
        print('cleaned up user:', username)
    else:
        print('no leftover user:', username)

# 汇总
print('\n==== E2E 结果 ====')
fails = [r for r in results if not r[0]]
for ok, name, extra in results:
    print(f'{"PASS" if ok else "FAIL"}  {name}{"  - " + str(extra) if extra and not ok else ""}')
print(f'\n总计 {len(results)} 项, 失败 {len(fails)} 项')
exit(1 if fails else 0)
