# 校园美食社交平台（CampusFood）

面向在校学生的**校园美食社区平台**：按学校发现食堂与周边美食、发表真实评价、发布探店笔记、关注博主、加入美食圈子、私信与校园群聊，首页带「规则 + 轻个性化」的推荐流。

## 功能亮点

- **学校维度内容**：全国 3000+ 高校名单导入，店铺/菜品/笔记/圈子全部以“学校”为内容边界
- **店铺 · 菜品 · 评价**：浏览、筛选、发表评价（自动维护平均分）
- **探店笔记**：发帖绑定店铺、点赞 / 收藏 / 评论 / 关注博主
- **实时社交**：美食圈子（QQ/微信群式）、一对一私信、全校群聊，基于 Flask-SocketIO + WebSocket
- **商户体系**：商户绑定店铺、学生可提交店铺与菜单（待审核流）
- **首页推荐流**：贝叶斯平滑评分 + 时间新鲜度 + 校内轻画像（收藏/好评/互动行为），登录个性化、游客/新用户退化为改进热门榜，每条推荐附可解释原因

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Vue Router + Pinia |
| 后端 | Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-JWT-Extended + Flask-SocketIO |
| 数据库 | MySQL 8 |
| 图片存储 | 本地 `backend/uploads/`，数据库保存相对路径 |

## 项目结构

```
├── backend/                  # Flask 后端
│   ├── app/
│   │   ├── __init__.py       # 应用工厂 create_app()
│   │   ├── config.py         # 分环境配置
│   │   ├── models/           # 数据模型（User/Shop/Dish/Post/Message/Circle…）
│   │   ├── routes/           # RESTful 路由（auth/shop/dish/post/chat/admin）
│   │   ├── services/         # 业务逻辑层（含推荐打分引擎 recommend_service.py）
│   │   ├── schemas/          # marshmallow 请求/响应校验
│   │   ├── utils/            # 统一响应/异常/装饰器/分页
│   │   └── extensions.py     # Flask 扩展实例（含 SocketIO）
│   ├── tests/                # 验证脚本（e2e / 推荐流）
│   ├── uploads/              # 图片上传目录（本地）
│   ├── requirements.txt
│   └── run.py                # 开发入口
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── api/              # axios 请求封装
│   │   ├── components/       # 公共组件（ShopCard/PostCard…）
│   │   ├── views/            # 页面（Home/Login/Shop/Post/Chat…）
│   │   ├── router/           # 路由与守卫
│   │   ├── store/            # Pinia 状态管理
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js        # /api 与 /socket.io 代理到后端
├── docker-compose.yml        # MySQL + 后端 + 前端 一键编排
└── README.md
```

## 快速开始（本地开发）

### 0. 准备数据库

```bash
# 本地 MySQL 8 创建数据库（按需修改密码）
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS campus_food DEFAULT CHARSET utf8mb4;"
```

### 1. 后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 修改数据库连接与密钥
python run.py               # 启动于 http://localhost:5000（自动建表）
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev                 # 启动于 http://localhost:5173（/api 与 /socket.io 已代理到后端）
```

### 3. 演示数据（可选）

后端提供若干幂等 CLI 种子命令，便于本地体验完整链路：

```bash
flask seed-demo        # 6 所演示学校 + 店铺
flask seed-posts       # 演示用户 + 探店笔记
flask seed-circles     # 演示圈子 + 私信/群聊消息
flask seed-rec-demo    # 独立「虚拟演示大学」+ 口味账号，验证首页推荐流效果
```

演示账号密码统一 `demo1234`。推荐流验证脚本见 `backend/tests/verify_rec_demo.py`。
