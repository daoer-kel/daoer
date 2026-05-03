from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import uuid

app = Flask(__name__)
CORS(app)

VIDEO_DIR = os.path.join('/tmp', 'videos')
os.makedirs(VIDEO_DIR, exist_ok=True)

@app.route('/api/parse', methods=['POST'])
def parse_video():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': '请提供视频链接'}), 400
        
        print(f'正在解析: {url}')
        video_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(VIDEO_DIR, f'{video_id}.%(ext)s')
        
        # 🔧 关键修复：添加浏览器伪装
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'socket_timeout': 30,
            'retries': 5,
            # 模拟真实浏览器
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # 添加常见请求头
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.bilibili.com/',
                'Origin': 'https://www.bilibili.com',
            },
        }
        
        # 获取视频标题
        with yt_dlp.YoutubeDL({'quiet': True, 'user_agent': ydl_opts['user_agent']}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
        
        # 下载视频
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 查找下载的文件
        downloaded_file = None
        for f in os.listdir(VIDEO_DIR):
            if f.startswith(video_id):
                downloaded_file = os.path.join(VIDEO_DIR, f)
                break
        
        if not downloaded_file:
            return jsonify({'error': '下载失败'}), 500
        
        filename = os.path.basename(downloaded_file)
        return jsonify({
            'success': True,
            'title': title,
            'videoUrl': f'/video/{filename}',
        })
        
    except Exception as e:
        print(f'错误: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/video/<filename>')
def serve_video(filename):
    filepath = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='video/mp4')
    return '文件不存在', 404

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'message': 'Daoer API is running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'Daoer API 正在启动，监听端口: {port}')
    app.run(host='0.0.0.0', port=port)
