"""Flask CLI 自定义命令（在 create_app 中注册）。

用法：
  flask seed-demo        # 写入演示用店铺数据（学校需先有数据）
  flask seed-dishes      # 为已有店铺写入演示用菜品
  flask seed-posts       # 写入演示用探店笔记 + 演示用户
  flask import-schools   # 从 data/schools.json 全量导入全国高校名单
"""
import json
import os

from app.extensions import db
from app.models import Comment, Dish, Like, Post, School, Shop, User


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
