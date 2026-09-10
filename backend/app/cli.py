"""Flask CLI 自定义命令（在 create_app 中注册）。

用法：
  flask seed-demo        # 写入演示用店铺数据（学校需先有数据）
  flask seed-dishes      # 为已有店铺写入演示用菜品
  flask seed-posts       # 写入演示用探店笔记 + 演示用户
  flask seed-merchant    # 写入演示商户账号并绑定一家店铺
  flask seed-admin       # 写入演示管理员账号
  flask seed-bot         # 写入官方消息机器人账号（自动回复私信）
  flask seed-circles     # 写入演示圈子 + 圈内群聊/私信/全校群聊消息
  flask seed-rec-demo    # 写入首页推荐流演示数据：独立虚拟学校 + 口味账号 + 店铺/菜品/笔记/行为
  flask import-schools   # 从 data/schools.json 全量导入全国高校名单
"""
import json
import os
import secrets
from datetime import datetime, timedelta

import click

from app.extensions import db
from app.models import (
    Circle,
    CircleMembership,
    Comment,
    Dish,
    EventLog,
    Favorite,
    Like,
    Message,
    Post,
    Review,
    School,
    Shop,
    User,
    UserFollow,
)


def register_cli(app) -> None:
    """注册全部自定义命令。"""

    @app.cli.command('seed-demo')
    def seed_demo():
        """写入演示数据：6 所学校 + 每校若干店铺（幂等，可重复执行）。"""
        schools = [
            {'name': '北京大学', 'address': '北京市'},
            {'name': '清华大学', 'address': '北京市'},
            {'name': '复旦大学', 'address': '上海市'},
            {'name': '浙江大学', 'address': '浙江省杭州市'},
            {'name': '武汉大学', 'address': '湖北省武汉市'},
            {'name': '中山大学', 'address': '广东省广州市'},
        ]

        shops_data = {
            '北京大学': [
                {'name': '北大农园食堂', 'category': '食堂', 'price_range': '10-20元', 'rating': 4.5, 'count': 128, 'address': '校园内农园路'},
                {'name': '畅春园食堂', 'category': '食堂', 'price_range': '8-18元', 'rating': 4.2, 'count': 96, 'address': '校园内畅春园'},
                {'name': '未名咖啡', 'category': '咖啡甜点', 'price_range': '20-40元', 'rating': 4.8, 'count': 210, 'address': '未名湖畔'},
                {'name': '燕园小面馆', 'category': '面食', 'price_range': '12-22元', 'rating': 4.0, 'count': 54, 'address': '南门商业街'},
            ],
            '清华大学': [
                {'name': '桃李园餐厅', 'category': '食堂', 'price_range': '10-20元', 'rating': 4.3, 'count': 87, 'address': '校园内桃李园'},
                {'name': '紫荆园食堂', 'category': '食堂', 'price_range': '8-16元', 'rating': 4.1, 'count': 110, 'address': '校园内紫荆公寓区'},
                {'name': '水木奶茶', 'category': '奶茶饮品', 'price_range': '15-25元', 'rating': 4.6, 'count': 176, 'address': '西门外商业街'},
                {'name': '清华西点屋', 'category': '烘焙甜点', 'price_range': '18-35元', 'rating': 4.7, 'count': 98, 'address': '校园内荷清园'},
            ],
            '复旦大学': [
                {'name': '旦苑餐厅', 'category': '食堂', 'price_range': '10-20元', 'rating': 4.2, 'count': 76, 'address': '邯郸校区'},
                {'name': '光华楼咖啡', 'category': '咖啡甜点', 'price_range': '22-45元', 'rating': 4.5, 'count': 132, 'address': '光华楼一层'},
                {'name': '江湾小食堂', 'category': '食堂', 'price_range': '8-15元', 'rating': 3.9, 'count': 45, 'address': '江湾校区'},
                {'name': '邯郸路生煎', 'category': '小吃', 'price_range': '10-18元', 'rating': 4.4, 'count': 89, 'address': '邯郸路商业街'},
            ],
            '浙江大学': [
                {'name': '紫金港食堂', 'category': '食堂', 'price_range': '9-18元', 'rating': 4.3, 'count': 143, 'address': '紫金港校区'},
                {'name': '西溪烘焙工坊', 'category': '烘焙甜点', 'price_range': '16-30元', 'rating': 4.6, 'count': 67, 'address': '西溪校区'},
                {'name': '求是奶茶', 'category': '奶茶饮品', 'price_range': '13-24元', 'rating': 4.5, 'count': 158, 'address': '玉泉校区北门'},
                {'name': '玉泉小面', 'category': '面食', 'price_range': '10-20元', 'rating': 4.1, 'count': 72, 'address': '玉泉校区'},
            ],
            '武汉大学': [
                {'name': '樱园食堂', 'category': '食堂', 'price_range': '8-15元', 'rating': 4.0, 'count': 66, 'address': '樱园宿舍区'},
                {'name': '珞珈山小火锅', 'category': '火锅', 'price_range': '40-70元', 'rating': 4.7, 'count': 185, 'address': '校门口商业街'},
                {'name': '武大咖小馆', 'category': '咖啡甜点', 'price_range': '18-32元', 'rating': 4.4, 'count': 93, 'address': '信息学部'},
                {'name': '工学部美食城', 'category': '美食广场', 'price_range': '12-25元', 'rating': 4.2, 'count': 121, 'address': '工学部'},
            ],
            '中山大学': [
                {'name': '康乐园食堂', 'category': '食堂', 'price_range': '9-16元', 'rating': 4.1, 'count': 88, 'address': '南校园'},
                {'name': '中大糖水铺', 'category': '甜品', 'price_range': '8-16元', 'rating': 4.8, 'count': 203, 'address': '北门美食街'},
                {'name': '东校区港式茶餐厅', 'category': '茶餐厅', 'price_range': '20-40元', 'rating': 4.5, 'count': 116, 'address': '东校区'},
                {'name': '珠江边烧烤', 'category': '烧烤', 'price_range': '30-60元', 'rating': 4.3, 'count': 77, 'address': '南门附近'},
            ],
        }

        # 幂等：已存在则跳过
        existing = School.query.filter(School.name.in_([s['name'] for s in schools])).count()
        if existing:
            print('检测到学校数据已存在，跳过写入。')
            return

        for s in schools:
            school = School(**s)
            db.session.add(school)
            db.session.flush()  # 拿到 school.id
            for sp in shops_data[s['name']]:
                db.session.add(Shop(
                    school_id=school.id,
                    name=sp['name'],
                    address=sp['address'],
                    category=sp['category'],
                    price_range=sp['price_range'],
                    avg_rating=sp['rating'],
                    rating_count=sp['count'],
                    image_url=f'https://picsum.photos/seed/{school.id}-{len(shops_data[s["name"]])}/400/300',
                ))

        db.session.commit()
        total_schools = School.query.count()
        total_shops = Shop.query.count()
        print(f'seed-demo 完成：{total_schools} 所学校，{total_shops} 家店铺。')

    @app.cli.command('import-schools')
    def import_schools():
        """从 data/schools.json 全量导入全国高校名单（按名称 upsert，替换演示数据）。"""
        path = os.path.join(os.path.dirname(app.root_path), 'data', 'schools.json')
        if not os.path.exists(path):
            print(f'未找到 {path}，请先执行 backend/data/build_schools_json.py 生成。')
            return
        with open(path, encoding='utf-8') as f:
            records = json.load(f)
        if not records:
            print('schools.json 为空，跳过。')
            return

        existing = {s.name: s for s in School.query.all()}
        names = {r['name'] for r in records}
        created = updated = deactivated = 0
        for rec in records:
            s = existing.get(rec['name'])
            if s is None:
                db.session.add(School(name=rec['name'], address=rec.get('address') or None))
                created += 1
            else:
                # 名称已存在（含 6 所演示学校）：更新为名单中的地址，并重新启用
                new_addr = rec.get('address') or s.address
                if s.address != new_addr or not s.is_active:
                    s.address = new_addr
                    s.is_active = True
                    updated += 1

        # 名单之外的旧学校停用（保留记录，避免店铺/用户外键悬挂）
        stale = [s for s in School.query.filter(School.is_active.is_(True)).all() if s.name not in names]
        for s in stale:
            s.is_active = False
            deactivated += 1

        db.session.commit()
        total = School.query.filter_by(is_active=True).count()
        print(f'import-schools 完成：新增 {created}，更新 {updated}，停用 {deactivated}；当前启用 {total} 所。')

    @app.cli.command('seed-dishes')
    def seed_dishes():
        """为已有店铺写入演示菜品（按分类匹配，幂等，可重复执行）。"""
        # 分类 -> 菜品（名称, 价格, 描述, 标签）
        dishes_by_category = {
            '食堂': [
                ('红烧肉盖饭', 14.5, '肥瘦相间，浓油赤酱，很下饭', '招牌,下饭'),
                ('番茄炒蛋盖饭', 11.0, '家常味道，酸甜可口', '清淡'),
                ('清蒸鱼套餐', 18.0, '鱼肉鲜嫩，配时蔬米饭', '清淡,高蛋白'),
                ('麻辣香锅', 22.0, '自选食材，麻辣鲜香', '辣,招牌'),
                ('素菜双拼', 8.5, '清爽素菜，健康管饱', '素食,清淡'),
            ],
            '面食': [
                ('兰州拉面', 15.0, '一清二白三红四绿五黄', '招牌,热卖'),
                ('牛肉刀削面', 18.0, '现削面条，劲道爽滑', '热卖'),
                ('老北京炸酱面', 14.0, '酱香浓郁，配黄瓜丝', '经典'),
            ],
            '咖啡甜点': [
                ('现磨拿铁', 18.0, '醇香咖啡配绵密奶泡', '热卖'),
                ('美式咖啡', 12.0, '清爽提神，低卡', '清淡'),
                ('提拉米苏', 22.0, '可可粉绵密口感', '甜点'),
            ],
            '奶茶饮品': [
                ('珍珠奶茶', 15.0, '经典黑糖珍珠', '招牌,冰饮'),
                ('芝士奶盖茶', 18.0, '咸香奶盖配清香茶底', '热卖'),
                ('百香果茶', 14.0, '酸甜清爽', '冰饮,果茶'),
            ],
            '烘焙甜点': [
                ('芝士蛋糕', 20.0, '入口即化的芝士香', '甜点,招牌'),
                ('可颂', 12.0, '层层酥脆黄油香', '早餐'),
                ('葡式蛋挞', 6.0, '外酥里嫩', '甜点,热卖'),
            ],
            '小吃': [
                ('生煎包', 10.0, '底部焦脆，汤汁鲜甜', '招牌,热卖'),
                ('煎饼果子', 8.0, '现摊薄饼，鸡蛋火腿', '早餐'),
                ('卤肉卷', 12.0, '卤香浓郁', '热卖'),
            ],
            '火锅': [
                ('鸳鸯锅底', 38.0, '一半麻辣一半清汤', '招牌,辣'),
                ('精品肥牛', 32.0, '纹理分明，涮八秒即熟', '招牌'),
                ('鲜毛肚', 28.0, '爽脆化渣', '招牌'),
                ('蔬菜拼盘', 18.0, '当日时蔬', '素食'),
            ],
            '烧烤': [
                ('羊肉串', 5.0, '孜然香辣，肥瘦相间', '招牌,辣'),
                ('烤鸡翅', 8.0, '外皮焦香多汁', '热卖'),
                ('烤茄子', 12.0, '蒜蓉香辣', '素食,辣'),
            ],
            '茶餐厅': [
                ('港式丝袜奶茶', 16.0, '茶味浓郁顺滑', '招牌,热饮'),
                ('菠萝油', 12.0, '酥皮配冰黄油', '经典'),
                ('干炒牛河', 28.0, '锅气十足', '招牌'),
            ],
            '甜品': [
                ('杨枝甘露', 18.0, '芒果西柚椰奶', '招牌,冰饮'),
                ('双皮奶', 12.0, '奶香浓郁', '经典'),
                ('红豆沙', 10.0, '绵密香甜', '热饮,清淡'),
            ],
            '美食广场': [
                ('麻辣烫', 20.0, '自选称重，汤底鲜美', '招牌,辣'),
                ('蛋包饭', 15.0, '蛋皮嫩滑，咖喱浓郁', '热卖'),
                ('关东煮', 12.0, '清汤鲜甜', '清淡'),
            ],
        }
        default_dishes = [
            ('招牌套餐', 20.0, '本店招牌，值得一试', '招牌'),
            ('特色小吃', 15.0, '店内特色', '热卖'),
        ]

        shops = Shop.query.filter_by(is_active=True).order_by(Shop.id.asc()).all()
        created = skipped = 0
        for shop in shops:
            if shop.dishes.count() > 0:
                skipped += 1
                continue
            dish_defs = dishes_by_category.get(shop.category) or default_dishes
            base_count = shop.rating_count or 50
            for i, (name, price, desc, tags) in enumerate(dish_defs):
                # 确定性伪随机评分：围绕 4.2 微调，避免每次重新执行结果不同
                variation = ((shop.id * 7 + i * 13) % 9 - 4) * 0.06
                rating = max(3.5, min(4.9, 4.2 + variation))
                db.session.add(Dish(
                    shop_id=shop.id,
                    name=name,
                    price=price,
                    description=desc,
                    tags=tags,
                    avg_rating=round(rating, 2),
                    rating_count=base_count + i * 17,
                    image_url=f'https://picsum.photos/seed/dish-{shop.id}-{i}/400/300',
                ))
                created += 1
        db.session.commit()
        total = Dish.query.filter_by(is_active=True).count()
        print(f'seed-dishes 完成：新增 {created} 道菜品，跳过 {skipped} 家已有菜品的店铺；当前共 {total} 道。')

    @app.cli.command('seed-posts')
    def seed_posts():
        """写入演示用探店笔记 + 演示用户（幂等，可重复执行）。"""
        if Post.query.filter_by(is_active=True).count() > 0:
            print('已存在笔记数据，跳过 seed-posts。')
            return

        # 演示用户（密码统一 demo1234）
        demo_users = [
            ('xiaolin', '美食家小林'),
            ('ajie', '吃货阿杰'),
            ('dawang', '干饭大王'),
        ]
        users = []
        for username, nickname in demo_users:
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username, nickname=nickname, role='student')
                user.set_password('demo1234')
                db.session.add(user)
                db.session.flush()
            users.append(user)

        # 笔记模板：标题, 正文, 标签, 店铺序数（取前若干家）
        post_templates = [
            ('食堂阿姨手抖？这家的红烧肉盖饭绝不手软',
             '北大农园食堂的红烧肉盖饭肥瘦相间，浓油赤酱，米饭浸满肉汁，一口下去幸福感拉满。中午 12 点前到不用排长队，强烈安利！',
             '食堂,安利', 0),
            ('宿舍楼下的生煎包，汤汁会爆！',
             '南门生煎包底煎得金黄酥脆，咬开是满满汤汁，小心烫嘴。配上一碗豆浆，完美早餐。',
             '小吃,早餐', 6),
            ('自习完来一杯热拿铁，回血神器',
             '未名咖啡的热拿铁拉花漂亮，奶泡绵密，自习一下午就靠它续命。靠窗的位置阳光正好。',
             '咖啡,自习', 2),
            ('周末火锅局，肥牛必须安排上',
             '珞珈山小火锅的精品肥牛纹理漂亮，涮八秒就熟，蘸麻酱一绝。人均 40-70 元，人多更划算。',
             '火锅,聚餐', 16),
            ('减脂期也可以吃得很满足',
             '食堂的素菜双拼清爽不油腻，加一份番茄炒蛋，营养又饱腹。健身党友好，价格也很友好。',
             '素食,减脂', 0),
            ('甜品星人冲！这家糖水铺真的绝',
             '杨枝甘露用料扎实，芒果新鲜，西柚微苦回甘，椰奶香浓。夏天来一碗瞬间降温。',
             '甜品,下午茶', 20),
            ('深夜食堂：关东煮配奶茶，治愈系',
             '美食城的关东煮汤头清甜，萝卜煮得通透入味。再点一杯珍珠奶茶，晚上饿的时候幸福感拉满。',
             '夜宵,治愈', 22),
            ('第一次在学校吃到这么正宗的兰州拉面',
             '现拉的拉面筋道，汤头清澈见底，牛肉片得薄而多。加一勺辣子，香而不燥。',
             '面食,招牌', 4),
            ('探店笔记：校园里的宝藏咖啡角',
             '这家咖啡店藏在角落里，环境安静，适合小组讨论。美式咖啡酸苦平衡，价格对学生党很友好。',
             '咖啡,探店', 1),
        ]

        shops = Shop.query.filter_by(is_active=True).order_by(Shop.id.asc()).all()
        created = 0
        for idx, (title, content, tags, shop_idx) in enumerate(post_templates):
            shop = shops[shop_idx % len(shops)] if shops else None
            if shop is None:
                continue  # 笔记必须关联店铺，无店铺则跳过
            author = users[idx % len(users)]
            post = Post(
                user_id=author.id,
                title=title,
                content=content,
                images=json.dumps([f'https://picsum.photos/seed/post-{idx}/800/500'], ensure_ascii=False),
                shop_id=shop.id,
                tags=tags,
                like_count=20 + idx * 7,
                favorite_count=8 + idx * 3,
            )
            db.session.add(post)
            db.session.flush()
            # 每篇演示笔记附 2 条评论
            for ci in range(2):
                commenter = users[(idx + ci + 1) % len(users)]
                db.session.add(Comment(
                    post_id=post.id,
                    user_id=commenter.id,
                    content='写得太真实了，周末就去试试！' if ci == 0 else '已收藏，改天约朋友一起去～',
                ))
            post.comment_count = 2
            created += 1
        db.session.commit()
        total = Post.query.filter_by(is_active=True).count()
        print(f'seed-posts 完成：新增 {created} 篇笔记；当前共 {total} 篇。演示用户密码均为 demo1234。')

    @app.cli.command('seed-merchant')
    def seed_merchant():
        """写入演示商户账号并绑定一家店铺（幂等，可重复执行）。"""
        demo_username = 'merchant'
        user = User.query.filter_by(username=demo_username).first()
        if user is None:
            user = User(username=demo_username, nickname='示例商户', role='merchant')
            user.set_password('demo1234')
            db.session.add(user)
            db.session.flush()

        if Shop.query.filter_by(owner_id=user.id).count() == 0:
            shop = Shop.query.filter_by(is_active=True).order_by(Shop.id.asc()).first()
            if shop is None:
                print('没有可绑定的店铺，请先执行 seed-demo。')
                return
            shop.owner_id = user.id

        db.session.commit()
        owned = Shop.query.filter_by(owner_id=user.id).count()
        print(f'seed-merchant 完成：演示商户 {demo_username}/demo1234（角色 merchant），已绑定 {owned} 家店铺。')

    @app.cli.command('seed-admin')
    def seed_admin():
        """写入演示管理员账号（幂等，可重复执行）。"""
        username = 'admin'
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, nickname='管理员', role='admin')
            user.set_password('demo1234')
            db.session.add(user)
            db.session.commit()
            print(f'seed-admin 完成：新增演示管理员 {username}/demo1234（角色 admin）。')
        else:
            print(f'seed-admin 完成：管理员 {username} 已存在，无需新增。')

    @app.cli.command('seed-bot')
    def seed_bot():
        """写入官方消息机器人账号（幂等，可重复执行）。

        机器人是普通用户账号（role='student'），靠保留用户名识别；
        密码取随机串，使其无法被登录，避免变成共享账号。
        """
        from app.services.bot_service import BOT_NICKNAME, BOT_USERNAME

        user = User.query.filter_by(username=BOT_USERNAME).first()
        if user is not None:
            print(f'seed-bot 完成：机器人 {BOT_USERNAME} 已存在，无需新增。')
            return

        user = User(
            username=BOT_USERNAME,
            nickname=BOT_NICKNAME,
            role='student',
        )
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
        db.session.commit()
        print(f'seed-bot 完成：新增官方助手 {BOT_USERNAME}（昵称「{BOT_NICKNAME}」，不可登录，自动回复私信）。')

    @app.cli.command('seed-circles')
    def seed_circles():
        """写入演示圈子 + 圈内群聊/私信/全校群聊消息（幂等，可重复执行）。"""
        if Circle.query.filter_by(is_active=True).count() > 0:
            print('已存在圈子数据，跳过 seed-circles。')
            return

        # 演示学校：优先北大（演示数据所在学校），否则取第一个启用学校
        school = School.query.filter_by(name='北京大学', is_active=True).first()
        if school is None:
            school = School.query.filter_by(is_active=True).order_by(School.id.asc()).first()
        if school is None:
            print('没有可用学校，请先执行 seed-demo。')
            return

        # 演示用户（密码统一 demo1234，绑定该校）
        demo_users = [
            ('xiaolin', '美食家小林'),
            ('ajie', '吃货阿杰'),
            ('dawang', '干饭大王'),
        ]
        users = []
        for username, nickname in demo_users:
            user = User.query.filter_by(username=username).first()
            if user is None:
                user = User(username=username, nickname=nickname, role='student')
                user.set_password('demo1234')
                db.session.add(user)
                db.session.flush()
            user.school_id = school.id
            users.append(user)

        # 三个演示圈子（群）：创建者均为 xiaolin
        circles_def = [
            ('夜宵党集结', '深夜觅食小分队，分享学校周边的深夜食堂与宵夜安利。', 'https://picsum.photos/seed/circle-1/600/300'),
            ('减脂餐打卡', '互相监督健康饮食，晒出你的减脂餐与食堂低卡组合。', 'https://picsum.photos/seed/circle-2/600/300'),
            ('食堂安利互助会', '哪个窗口最值得排队？新菜品评测交流群。', 'https://picsum.photos/seed/circle-3/600/300'),
        ]
        circles = []
        for i, (name, desc, cover) in enumerate(circles_def):
            circle = Circle(
                school_id=school.id,
                creator_id=users[0].id,
                name=name,
                description=desc,
                cover_url=cover,
                member_count=len(users),
            )
            db.session.add(circle)
            db.session.flush()
            circles.append(circle)
            for u in users:
                db.session.add(CircleMembership(circle_id=circle.id, user_id=u.id))

        # 圈1 群聊消息
        group_chat = [
            (users[0], '今晚 11 点有没有人组队去南门吃烧烤？'),
            (users[1], '算我一个！上次那家烤鸡翅绝了。'),
            (users[2], '加一，顺便带杯奶茶。'),
            (users[0], '好，那就老地方见，不见不散～'),
        ]
        # 私信：xiaolin <-> ajie
        dms = [
            (users[0], users[1], '你上次推荐的那家生煎在哪来着？'),
            (users[1], users[0], '南门进去右手边那家，记得趁热吃！'),
            (users[0], users[1], '收到，明天早餐就它了，谢啦！'),
            (users[2], users[0], '（未读示例）兄弟，周五要不要一起去探店？'),  # 给 xiaolin 一条未读私信
        ]
        # 全校群聊消息
        school_chat = [
            (users[0], '有没有同学捡到一张校园卡？名字是李某某。'),
            (users[1], '看到的话交到一食堂服务台哦。'),
        ]
        created = 0
        for u, content in group_chat:
            db.session.add(Message(user_id=u.id, circle_id=circles[0].id, content=content))
            created += 1
        for sender, recipient, content in dms:
            db.session.add(Message(user_id=sender.id, recipient_id=recipient.id, content=content))
            created += 1
        for u, content in school_chat:
            db.session.add(Message(user_id=u.id, school_id=school.id, content=content))
            created += 1

        db.session.commit()
        total_circles = Circle.query.filter_by(is_active=True).count()
        total_messages = Message.query.count()
        print(
            f'seed-circles 完成：新增 {total_circles} 个圈子、{len(users)} 名成员绑定，'
            f'{created} 条消息；当前消息共 {total_messages} 条。'
        )

    @app.cli.command('seed-rec-demo')
    def seed_rec_demo():
        """写入首页推荐流（A+B 算法）演示数据：独立虚拟学校 + 口味账号 + 店铺/菜品/笔记/行为（幂等）。"""
        if School.query.filter_by(name='虚拟演示大学').first() is not None:
            print('检测到虚拟演示大学已存在，跳过 seed-rec-demo。')
            return

        school = School(name='虚拟演示大学', address='演示用虚拟校区')
        db.session.add(school)
        db.session.flush()
        now = datetime.utcnow()

        def days_ago(days):
            return now - timedelta(days=float(days))

        # ---- 演示用户（密码统一 demo1234，全部绑定虚拟校）----
        def make_user(username, nickname):
            user = User(username=username, nickname=nickname, role='student', school_id=school.id)
            user.set_password('demo1234')
            db.session.add(user)
            db.session.flush()
            return user

        author1 = make_user('rec_author1', '川味探店佬')   # 川菜店主 + 作者
        author2 = make_user('rec_author2', '奶茶测评员')   # 奶茶店主 + 作者
        author3 = make_user('rec_author3', '食堂情报员')   # 食堂/甜品作者
        spicy = make_user('rec_spicy', '无辣不欢')         # 川菜口味账号
        milk = make_user('rec_milk', '奶茶续命')           # 奶茶口味账号
        cold = make_user('rec_cold', '新来的小透明')       # 零行为（冷启动对照组）
        ghost = make_user('rec_ghost', '幽灵评审员')       # 给陷阱店刷出那唯一一条 5.0 评分

        # ---- 店铺（is_active=True / status=approved 之外设两个反例店验证过滤）----
        shops = []

        def make_shop(name, category, rating, count, created_days, owner=None,
                      status='approved', active=True, price='10-20元'):
            shop = Shop(
                school_id=school.id,
                name=name,
                category=category,
                price_range=price,
                address=f'{school.name}·{name}',
                avg_rating=rating,
                rating_count=count,
                image_url=f'https://picsum.photos/seed/vshop-{len(shops) + 1}/400/300',
                created_at=days_ago(created_days),
                owner_id=owner.id if owner else None,
                status=status,
                is_active=active,
            )
            db.session.add(shop)
            db.session.flush()
            shops.append(shop)
            return shop

        dining = make_shop('虚拟第一食堂', '食堂', 4.8, 350, 1)                        # 校内热度第一
        laojie = make_shop('虚拟老街川菜馆', '川菜', 4.5, 120, 12, owner=author1)       # 川菜（店主被 spicy 关注）
        bashu = make_shop('虚拟巴蜀小厨', '川菜', 4.4, 90, 20, owner=author1)
        maocai = make_shop('虚拟川香冒菜', '川菜', 4.6, 70, 8)
        naigai = make_shop('虚拟奶盖研究所', '奶茶', 4.6, 100, 6, owner=author2)        # 奶茶（店主被 milk 关注）
        boba = make_shop('虚拟波霸奶茶', '奶茶', 4.5, 80, 18, owner=author2)
        yikoutian = make_shop('虚拟一口甜奶茶', '奶茶', 4.4, 60, 30)
        salad = make_shop('虚拟轻食沙拉坊', '轻食', 0.0, 0, 2)                          # 陷阱店：0 评起，由幽灵评审刷到 5.0/1
        dessert = make_shop('虚拟港岛甜品', '甜品', 4.7, 150, 25)                      # 高人气干扰项
        make_shop('虚拟待审烧烤摊', '烧烤', 5.0, 1, 1, status='pending')               # 反例：待审核必须被排除
        make_shop('虚拟已下架面馆', '面食', 4.9, 500, 40, active=False)                # 反例：下架必须被排除

        # 幽灵评审给陷阱店刷那一条 5.0（用服务层公式从 0 起步，保证 review 行与均分一致）
        salad.rating_count += 1
        salad.avg_rating = (salad.avg_rating * (salad.rating_count - 1) + 5) / salad.rating_count
        db.session.add(Review(user_id=ghost.id, shop_id=salad.id, rating=5, content='新店试吃，环境干净味道在线。'))

        # ---- 菜品：tags 用规范 token；奶茶店 avg 压低让「父店偏好 + 标签重合」主导 ----
        dish_defs = {
            dining: [
                ('红烧肉盖饭', 15.0, '招牌,下饭', 4.7, 180, 2),
                ('番茄炒蛋套餐', 12.0, '清淡,家常', 4.5, 120, 5),
            ],
            laojie: [
                ('水煮牛肉', 32.0, '辣,招牌', 4.6, 90, 4),
                ('麻婆豆腐', 16.0, '辣,下饭', 4.4, 70, 9),
            ],
            bashu: [
                ('辣子鸡', 26.0, '辣,招牌', 4.5, 60, 7),
                ('回锅肉', 22.0, '辣,家常', 4.3, 50, 14),
            ],
            maocai: [
                ('麻辣冒菜', 18.0, '辣,冒菜', 4.6, 40, 6),
                ('番茄冒菜', 18.0, '清淡,冒菜', 4.2, 30, 11),
            ],
            naigai: [
                ('黑糖珍珠奶茶', 14.0, '珍珠,奶茶,招牌', 4.4, 80, 3),
                ('芝士奶盖茶', 16.0, '奶盖,奶茶', 4.3, 60, 6),
            ],
            boba: [
                ('波霸招牌奶茶', 15.0, '珍珠,奶茶,招牌', 4.4, 70, 5),
                ('冰淇淋椰奶', 13.0, '冰饮,奶茶', 4.2, 40, 10),
            ],
            yikoutian: [
                ('一口甜珍奶', 12.0, '珍珠,奶茶', 4.3, 50, 9),
                ('抹茶拿铁奶茶', 15.0, '奶盖,奶茶', 4.1, 30, 15),
            ],
            salad: [
                ('鸡胸肉轻食沙拉', 18.0, '低卡,轻食', 4.6, 1, 2),
            ],
            dessert: [
                ('杨枝甘露', 18.0, '招牌,冰饮', 4.7, 90, 8),
                ('港式双皮奶', 12.0, '甜品,经典', 4.5, 70, 12),
            ],
        }
        dish_count = 0
        for shop, defs in dish_defs.items():
            for name, price, tags, avg, count, created_days in defs:
                db.session.add(Dish(
                    shop_id=shop.id,
                    name=name,
                    price=price,
                    tags=tags,
                    avg_rating=avg,
                    rating_count=count,
                    description=f'{shop.name}招牌',
                    image_url=f'https://picsum.photos/seed/vdish-{len(dish_defs)}{name}/400/300',
                    created_at=days_ago(created_days),
                ))
                dish_count += 1

        # ---- 探店笔记（作者/热度/新旧错开；tags 为规范 token 供画像标签重合）----
        post_defs = [
            (author3, dining, '食堂中午永远排队的红烧肉，真香', '食堂,实惠,下饭', 90, 30, 10, 0.5),
            (author1, laojie, '老街川菜的水煮牛肉，重口星人狂喜', '川菜,重辣,下饭', 40, 15, 5, 3),
            (author1, bashu, '巴蜀小厨的辣子鸡，酥脆到骨头都能嚼', '川菜,家常', 30, 10, 3, 6),
            (author3, maocai, '一人食冒菜，麻辣鲜香刚刚好', '川菜,冒菜', 15, 5, 1, 12),
            (author2, naigai, '奶盖研究所的芝士奶盖茶，咸香不腻', '奶茶,奶盖,冰饮', 70, 25, 8, 2),
            (author2, boba, '波霸奶茶大测评：黑糖味最正', '珍珠,奶茶', 45, 12, 4, 5),
            (author3, yikoutian, '一口甜珍奶，校园平价快乐水', '奶茶,招牌', 20, 6, 2, 15),
            (author3, dessert, '港岛甜品的杨枝甘露，芒果给得很足', '甜品,下午茶,冰饮', 55, 20, 6, 4),
            (author1, salad, '减脂期友好：这家轻食沙拉意外好吃', '轻食,减脂', 10, 2, 0, 1),
        ]
        posts = []
        for author, shop, title, tags, likes, favs, comments, created_days in post_defs:
            post = Post(
                user_id=author.id,
                shop_id=shop.id,
                title=title,
                content=f'{title}——来自 {school.name} 的探店实测。',
                images=json.dumps([f'https://picsum.photos/seed/vpost-{len(posts)}/800/500'], ensure_ascii=False),
                tags=tags,
                like_count=likes,
                favorite_count=favs,
                comment_count=comments,
                created_at=days_ago(created_days),
            )
            db.session.add(post)
            db.session.flush()
            posts.append(post)

        # ---- 行为（画像证据：收藏店 / 好评店 / 点赞·收藏帖 / 关注作者）----
        def add_review(user, shop, rating, content='好吃，值得再刷！'):
            """行为 Review 落库时同步按服务层公式维护店铺均分。"""
            shop.rating_count += 1
            shop.avg_rating = (shop.avg_rating * (shop.rating_count - 1) + rating) / shop.rating_count
            db.session.add(Review(user_id=user.id, shop_id=shop.id, rating=rating, content=content))

        def add_favorite_shop(user, shop):
            db.session.add(Favorite(user_id=user.id, shop_id=shop.id))

        # rec_spicy（无辣不欢）：川菜偏好
        add_favorite_shop(spicy, laojie)
        add_favorite_shop(spicy, bashu)
        add_review(spicy, maocai, 5, '冒菜香辣过瘾，一个人也能吃得爽。')
        db.session.add(Like(user_id=spicy.id, post_id=posts[1].id))     # 川菜帖
        db.session.add(Favorite(user_id=spicy.id, post_id=posts[2].id))  # 川菜帖
        db.session.add(UserFollow(follower_id=spicy.id, followee_id=author1.id))

        # rec_milk（奶茶续命）：奶茶偏好
        add_favorite_shop(milk, naigai)
        add_favorite_shop(milk, boba)
        add_review(milk, yikoutian, 5, '奶味足、不齁甜，续命神器。')
        db.session.add(Like(user_id=milk.id, post_id=posts[4].id))      # 奶茶帖
        db.session.add(Favorite(user_id=milk.id, post_id=posts[5].id))  # 奶茶帖
        db.session.add(UserFollow(follower_id=milk.id, followee_id=author2.id))

        # rec_cold：零行为（冷启动对照）

        db.session.commit()

        active_shops = Shop.query.filter_by(school_id=school.id, is_active=True, status='approved').count()
        print(
            f'seed-rec-demo 完成：学校「{school.name}」+ 7 名演示账号（密码 demo1234）；'
            f'启用店铺 {active_shops} 家、菜品 {dish_count} 道、笔记 {len(posts)} 篇。'
        )
        print('用法：进入首页选「虚拟演示大学」，用 rec_spicy / rec_milk / rec_cold 登录对比三轨推荐差异。')

    @app.cli.command('normalize-categories')
    @click.option('--dry-run', is_flag=True, help='只打印回填计划与残留清单，不写库。')
    def normalize_categories(dry_run):
        """店铺分类回填 + 熵审计：把别名类刷成规范值，并报告归不进词表的残留店（幂等）。

        词表/别名见 app.categories；残留店（如历史垃圾值）不会被自动改写，打印后
        用管理员归类接口 `PUT /api/admin/shops/<id>/category` 人工处置。
        """
        from sqlalchemy import func

        from app.categories import CATEGORY_SET, canonicalize

        counts = db.session.query(Shop.category, func.count(Shop.id)).group_by(Shop.category).all()
        print('—— 当前 category 分布 ——')
        for cat, n in sorted(counts, key=lambda t: (t[0] is None, str(t[0]) or '')):
            print(f'  {str(cat):<10} ×{n}')

        plan = []      # (旧值, 规范值, 家数)
        leftovers = []  # (id, name, 旧分类)：归不进词表，待管理员人工归类
        for cat, n in counts:
            if cat is None or not str(cat).strip():
                continue
            canon = canonicalize(cat)
            if canon not in CATEGORY_SET:
                for shop in Shop.query.filter(Shop.category == cat).order_by(Shop.id.asc()).all():
                    leftovers.append((shop.id, shop.name, shop.category))
            elif canon != cat:
                plan.append((cat, canon, n))

        print('\n—— 回填计划（别名 → 规范值）——')
        if plan:
            for old, new, n in plan:
                print(f'  {old} → {new}　×{n} 家')
        else:
            print('  无需回填（已全部规范）')

        if leftovers:
            print('\n—— 归不进词表的残留店（需管理员归类，可用 reclassify 接口或直接改库）——')
            for sid, name, old in leftovers:
                print(f'  id={sid}　「{name}」　旧分类={old}')

        if dry_run:
            print('\n[dry-run] 未写库。')
            return

        if plan:
            for old, new, _ in plan:
                Shop.query.filter(Shop.category == old).update({Shop.category: new})
            db.session.commit()
            print(f'\n已回填 {sum(n for _, _, n in plan)} 家（{len(plan)} 类别名）。')
        print(f'当前非规范残留 {len(leftovers)} 家。')

    @app.cli.command('seed-events')
    def seed_events():
        """回填近 30 天演示埋点事件，供管理员「数据统计」看板展示（幂等：已有事件则跳过）。"""
        if EventLog.query.count() > 0:
            print('检测到 event_logs 已存在，跳过 seed-events。')
            return

        schools = School.query.filter_by(is_active=True).all()
        if not schools:
            print('没有学校数据，请先运行 flask seed-demo 再执行本命令。')
            return

        users = User.query.all()
        admin = next((u for u in users if u.role == 'admin'), users[0] if users else None)
        shops = Shop.query.filter_by(is_active=True).all()
        dishes = Dish.query.filter_by(is_active=True).all()
        posts = Post.query.filter_by(is_active=True).all()

        now = datetime.utcnow()

        def add_event(event_type, target_type, target_id, school, days_back, extra=None):
            log = EventLog(
                actor_id=admin.id if admin else None,
                actor_role=admin.role if admin else None,
                event_type=event_type,
                target_type=target_type,
                target_id=target_id,
                school_id=school.id if school else None,
                extra=json.dumps(extra, ensure_ascii=False) if extra else None,
                created_at=now - timedelta(days=days_back),
            )
            db.session.add(log)

        # 店铺：提交 + 通过（少量驳回）
        for i, shop in enumerate(shops[:10]):
            school = shop.school or schools[i % len(schools)]
            days = (i * 3 % 28) + 1
            add_event('shop_submit', 'shop', shop.id, school, days,
                      {'name': shop.name, 'category': shop.category})
            if i % 5 == 0:
                add_event('shop_reject', 'shop', shop.id, school, days - 0.5,
                          {'name': shop.name, 'reason': '资料不完整'})
            else:
                add_event('shop_approve', 'shop', shop.id, school, days - 0.5, {'name': shop.name})

        # 菜品：提交 + 通过（少量驳回）
        for i, dish in enumerate(dishes[:16]):
            school = dish.shop.school if dish.shop else schools[i % len(schools)]
            days = (i * 2 % 27) + 1
            add_event('dish_submit', 'dish', dish.id, school, days, {'name': dish.name})
            if i % 6 == 0:
                add_event('dish_reject', 'dish', dish.id, school, days - 0.5,
                          {'name': dish.name, 'reason': '图片缺失'})
            else:
                add_event('dish_approve', 'dish', dish.id, school, days - 0.5, {'name': dish.name})

        # 笔记：发布
        for i, post in enumerate(posts[:8]):
            school = post.shop.school if post.shop else schools[i % len(schools)]
            days = (i * 4 % 25) + 1
            add_event('post_create', 'post', post.id, school, days, {'title': post.title})

        db.session.commit()
        print(f'seed-events 完成：回填 {EventLog.query.count()} 条事件（近 30 天），供管理员「数据统计」看板展示。')
