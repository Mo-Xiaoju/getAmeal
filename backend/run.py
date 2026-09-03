"""开发环境入口：python run.py

用 SocketIO 启动（内部包装 werkzeug + simple-websocket，threading 模式）。
部署切换 gunicorn 时需用 eventlet worker，见部署备注。
"""
import os

from app import create_app
from app.extensions import sio

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


if __name__ == '__main__':
    sio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
