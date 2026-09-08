"""图片上传与静态回显。

上传统一走 /api/upload（任意登录角色可用：头像、店铺/菜品封面、圈子封面、笔记多图都用它），
返回相对 URL `/api/uploads/<uuid>.<ext>`——dev（Vite /api 代理）与生产（nginx location /api/）
均已具备回源能力，无需额外代理。

文件落 backend/uploads/（gitignore 放行）；仅白名单扩展名 + UUID 命名 + 16MB 上限。
"""
import os
import uuid

from flask import Blueprint, current_app, request, send_from_directory

from app.utils.decorators import require_login
from app.utils.exceptions import ValidationError
from app.utils.responses import ok

bp_media = Blueprint('media', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@bp_media.route('/upload', methods=['POST'])
@require_login
def upload_image():
    """上传一张本地图片，返回其访问 URL。"""
    file = request.files.get('file')
    if file is None or not file.filename:
        raise ValidationError(message='未选择文件', code=4000)
    ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(message='仅支持 png / jpg / jpeg / gif / webp 图片格式', code=4000)

    folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(folder, exist_ok=True)
    name = f'{uuid.uuid4().hex}.{ext}'
    file.save(os.path.join(folder, name))
    return ok({'url': f'/api/uploads/{name}'}, message='上传成功')


@bp_media.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """公开回显上传图片（展示组件无鉴权加载）。"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
