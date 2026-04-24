import os
import asyncio
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from pathlib import Path

from config import get_settings, ensure_directories
from api.routes import api_bp


settings = get_settings()
ensure_directories()


app = Flask(
    __name__,
    template_folder=str(settings.BASE_DIR / 'templates'),
    static_folder=str(settings.BASE_DIR / 'static')
)

CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False


app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        app.static_folder,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT
    })


@app.route('/data/images/<filename>')
def serve_images(filename):
    return send_from_directory(settings.IMAGES_DIR, filename)


@app.route('/data/audio/<filename>')
def serve_audio_files(filename):
    return send_from_directory(settings.AUDIO_DIR, filename)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "资源不存在",
        "code": 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "服务器内部错误",
        "code": 500
    }), 500


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": "请求参数错误",
        "code": 400
    }), 400


def run_server():
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎨 WordVivid - AI多模态背诵辅助工具                        ║
║                                                              ║
║   服务已启动!                                                 ║
║   访问地址: http://localhost:{settings.PORT}                     ║
║                                                              ║
║   API文档: http://localhost:{settings.PORT}/api/health          ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        threaded=True
    )


if __name__ == '__main__':
    run_server()
