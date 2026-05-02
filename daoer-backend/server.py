from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import uuid

app = Flask(__name__)
CORS(app)

# 使用 /tmp 目录（Railway 可写）
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
        
        # 获取视频标题
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
        
        # 下载配置（云端不需要指定 ffmpeg 路径）
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'socket_timeout': 30,
            'retries': 3,
        }
        
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
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
