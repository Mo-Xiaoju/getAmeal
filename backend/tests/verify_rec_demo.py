"""首页推荐流（A+B）验证脚本：对着 seed-rec-demo 造出的虚拟数据断言算法行为。

先决条件：
  flask seed-rec-demo   （幂等，已执行）
  后端 API 可达（默认 http://localhost:5000/api，若不可达自动退回 :5173 Vite 代理）

覆盖：
  a. spicy(川菜) 与 milk(奶茶) 的店铺推荐榜首分类不同
  b. 各自的顶类符合画像，且个性化 reason 非空
  c. 游客与 rec_cold 冷启动返回一致的热门榜；5.0/1 陷阱店不置顶；无 pending/下架店
  d. milk 的菜品轨 top6 中 >=3/6 来自奶茶父店
  e. /posts?sort=recommend 两账号结果不同且全部学校隔离；sort=newest 语义不变
  f. 回归：无 token 的 /shops/recommend、/dishes/recommend、/posts?sort=recommend 均不 401
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = []
VIRTUAL_SCHOOL = '虚拟演示大学'
PWD = 'demo1234'
MILK_SHOPS = {'虚拟奶盖研究所', '虚拟波霸奶茶', '虚拟一口甜奶茶'}


def _base():
    for port in (5000, 5173):
        try:
            urllib.request.urlopen(f'http://localhost:{port}/api/schools', timeout=3)
            return f'http://localhost:{port}/api'
        except Exception:
            continue
    raise SystemExit('后端 API 不可达（请先启动后端 :5000）')


BASE = _base()


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
    return body.get('data'), body.get('code'), body.get('message')


def check(name, cond, extra=''):
    results.append((bool(cond), name, '' if cond else (extra or 'FAIL')))


def login(username):
    data, code, msg = call('POST', '/auth/login',
                           payload={'username': username, 'password': PWD})
    if code != 0 or not data or not data.get('access_token'):
        check(f'login {username}', False, msg or 'no token')
        return None
    return data['access_token']


# 0. 找到虚拟演示大学
data, code, msg = call('GET', '/schools')
schools = {s['name']: s['id'] for s in (data or [])}
check('虚拟演示大学 存在', VIRTUAL_SCHOOL in schools)
sid = schools.get(VIRTUAL_SCHOOL)
if sid is None:
    print('\n==== 无法继续（缺少 seed-rec-demo 数据）====')
    exit(1)

spicy_tok = login('rec_spicy')
milk_tok = login('rec_milk')
cold_tok = login('rec_cold')
if not (spicy_tok and milk_tok and cold_tok):
    print('\n==== 账号登录失败，请确认 seed-rec-demo 已执行 ====')
    exit(1)

# ---- a/b. 店铺轨个性化 ----
s_spicy, code, msg = call('GET', f'/shops/recommend?school_id={sid}&page_size=6', token=spicy_tok)
s_milk, code, msg = call('GET', f'/shops/recommend?school_id={sid}&page_size=6', token=milk_tok)
items_s = s_spicy.get('items', []) or []
items_m = s_milk.get('items', []) or []
check('spicy 店铺推荐非空', len(items_s) >= 1, f'len={len(items_s)}')
check('milk 店铺推荐非空', len(items_m) >= 1, f'len={len(items_m)}')
if items_s and items_m:
    top_cat_s, top_cat_m = items_s[0].get('category'), items_m[0].get('category')
    check('榜首分类不同(spicy/milk)', top_cat_s != top_cat_m, f'{top_cat_s} vs {top_cat_m}')
    check('spicy 顶类=川菜', top_cat_s == '川菜', str(top_cat_s))
    check('milk 顶类=奶茶', top_cat_m == '奶茶', str(top_cat_m))
check('spicy reason 非空', bool(items_s and items_s[0].get('rec_reason')), str(items_s[0].get('rec_reason') if items_s else None))
check('milk reason 非空', bool(items_m and items_m[0].get('rec_reason')), str(items_m[0].get('rec_reason') if items_m else None))

# ---- c. 冷启动：游客 == rec_cold；陷阱店不置顶；无待审/下架 ----
s_guest, code, msg = call('GET', f'/shops/recommend?school_id={sid}&page_size=6')
s_cold, code, msg = call('GET', f'/shops/recommend?school_id={sid}&page_size=6', token=cold_tok)
guest_ids = [it['id'] for it in (s_guest.get('items', []) or [])]
cold_ids = [it['id'] for it in (s_cold.get('items', []) or [])]
check('游客返回 6 项', len(guest_ids) == 6, f'len={len(guest_ids)}')
check('游客 == rec_cold 顺序', guest_ids == cold_ids, f'{guest_ids} vs {cold_ids}')
if s_guest and s_guest.get('items'):
    names = [it['name'] for it in s_guest['items']]
    check('5.0/1 陷阱店不置顶', s_guest['items'][0]['name'] != '虚拟轻食沙拉坊', names[0])
    check('无 pending/下架店铺', not ({'虚拟待审烧烤摊', '虚拟已下架面馆'} & set(names)), str(names))
    check('店铺均为 approved', all(it.get('status') == 'approved' for it in s_guest['items']))

# ---- d. milk 菜品轨：>=3/6 来自奶茶父店 ----
d_milk, code, msg = call('GET', f'/dishes/recommend?school_id={sid}&limit=6', token=milk_tok)
milk_dish_count = sum(1 for it in (d_milk.get('items', []) or []) if it.get('shop_name') in MILK_SHOPS)
check('milk 菜品轨 top6 中奶茶父店 >=3', milk_dish_count >= 3, f'{milk_dish_count}/6: '
      + str([it.get('shop_name') for it in (d_milk.get('items', []) or [])]))

# ---- e. 笔记轨 recommend 个性化 + 学校隔离 + newest 不变 ----
p_spicy, code, msg = call('GET', f'/posts?school_id={sid}&page_size=6&sort=recommend', token=spicy_tok)
p_milk, code, msg = call('GET', f'/posts?school_id={sid}&page_size=6&sort=recommend', token=milk_tok)
spicy_post_ids = [p['id'] for p in (p_spicy.get('items', []) or [])]
milk_post_ids = [p['id'] for p in (p_milk.get('items', []) or [])]
check('posts sort=recommend 均可用', code == 0 and spicy_post_ids and milk_post_ids,
      f'spicy={len(spicy_post_ids)}, milk={len(milk_post_ids)}')
check('spicy/milk 笔记推荐不同', spicy_post_ids != milk_post_ids, f'{spicy_post_ids} vs {milk_post_ids}')
for label, plist in (('spicy', p_spicy), ('milk', p_milk)):
    shop_names = {p.get('shop_name') for p in (plist.get('items', []) or [])}
    # 虚拟校的 9 家 approved 店铺全部带「虚拟」前缀；若混入其它学校则为空/非虚拟
    check(f'posts {label} 学校隔离', bool(shop_names) and all(n and '虚拟' in n for n in shop_names), str(shop_names))

p_newest, code, msg = call('GET', f'/posts?school_id={sid}&page_size=6&sort=newest')
newest_times = [p['created_at'] for p in (p_newest.get('items', []) or [])]
check('sort=newest 语义不变', newest_times == sorted(newest_times, reverse=True), str(newest_times[:2]))

# ---- f. 回归：无 token 的推荐入口不 401，仍返回默认条数 ----
data, code, msg = call('GET', f'/shops/recommend?school_id={sid}')
check('无token /shops/recommend code=0', code == 0, f'code={code} {msg}')
check('无token 返回 6 项', len((data.get('items', []) or [])) == 6, f'len={len(data.get("items", []) or [])}')
data, code, msg = call('GET', f'/dishes/recommend?school_id={sid}')
check('无token /dishes/recommend code=0', code == 0, f'code={code} {msg}')
data, code, msg = call('GET', f'/posts?school_id={sid}&sort=recommend')
check('无token /posts sort=recommend code=0', code == 0, f'code={code} {msg}')
data, code, msg = call('GET', '/shops/recommend')
check('无token /shops/recommend 全校可访问', code == 0, f'code={code} {msg}')

# 汇总
print('\n==== 推荐流验证结果 ====')
fails = [r for r in results if not r[0]]
for ok, name, extra in results:
    print(f'{"PASS" if ok else "FAIL"}  {name}' + (f'  - {extra}' if extra and not ok else ''))
print(f'\n总计 {len(results)} 项, 失败 {len(fails)} 项')
exit(1 if fails else 0)
