# 校园美食 · 后端镜像（Flask + Gunicorn）
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先安装依赖，利用镜像层缓存
COPY requirements.txt .
RUN pip install -r requirements.txt

# 拷贝应用代码
COPY . .

EXPOSE 5000

# 生产模式 Gunicorn（compose 中可通过 command 覆盖）
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:create_app()"]
