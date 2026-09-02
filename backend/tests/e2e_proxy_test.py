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


def call(method, path, token=None, payload=None, expect=0):
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

# 12. 删除评价（清理）
data, code, msg = call('GET', '/user/reviews?page=1&page_size=5', token=token)
rid = data['items'][0]['id']
data, code, msg = call('DELETE', f'/user/reviews/{rid}', token=token)
check('delete review ok', code == 0)

# 13. 清理测试账号（删除用户；收藏/评价已在上方移除，服务层会同步回滚店铺评分）
from app import create_app
from app.models import User
from app.extensions import db

app = create_app('development')
with app.app_context():
    u = User.query.filter_by(username=username).first()
    if u:
        # 若有未清收藏先删（本流程已取消），再删用户
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
