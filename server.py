"""
AutoScriptor Local Server
Полноценный локальный сервер AutoScriptor с поддержкой:
- Проксирования API запросов (без ограничений CORS)
- Нейроозвучки сценариев (Microsoft Edge-TTS)
- Автоматического рендеринга видео 9:16 с виральными субтитрами через FFmpeg
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import subprocess
import json
import webbrowser
import os
import sys
import shutil
import re
import uuid

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(DIRECTORY, "media")

# Создаем папку для медиафайлов
os.makedirs(MEDIA_DIR, exist_ok=True)

def find_ffmpeg():
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    py_dir = os.path.dirname(sys.executable)
    candidate = os.path.join(py_dir, "Scripts", "ffmpeg.exe")
    if os.path.exists(candidate):
        return candidate
    return "ffmpeg"

FFMPEG_BIN = find_ffmpeg()

def get_audio_duration(audio_path):
    cmd = [FFMPEG_BIN, '-i', audio_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', res.stderr)
    if m:
        h, m, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + m * 60 + s
    return 5.0

def create_subtitles(text, duration, ass_path):
    """Генерирует динамичные субтитры в формате ASS со стилем виральных Shorts"""
    # Очищаем сценарий от Markdown, скобок и ремарок
    clean = re.sub(r'\[.*?\]', '', text)
    clean = re.sub(r'\(.*?\)', '', clean)
    clean = re.sub(r'#+\s*', '', clean)
    
    words = clean.split()
    chunks = []
    curr = []
    for w in words:
        curr.append(w)
        # Группируем по 3-5 слов или по знакам препинания для высокого темпа
        if len(curr) >= 4 or w.endswith(('.', '!', '?', ':', ';')):
            chunks.append(' '.join(curr))
            curr = []
    if curr:
        chunks.append(' '.join(curr))
    
    total_chars = max(1, sum(len(c) for c in chunks))
    time_per_char = duration / total_chars

    ass_lines = [
        '[Script Info]',
        'ScriptType: v4.00+',
        'PlayResX: 720',
        'PlayResY: 1280',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Default,Arial,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,0,2,30,30,340,1',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text'
    ]

    def fmt(t):
        m = int(t // 60)
        s = t % 60
        return f"0:{m:02d}:{s:05.2f}"

    cur_time = 0.0
    for c in chunks:
        chunk_dur = len(c) * time_per_char
        start_t = cur_time
        end_t = min(duration, cur_time + chunk_dur)
        cur_time = end_t
        ass_lines.append(f"Dialogue: 0,{fmt(start_t)},{fmt(end_t)},Default,,0,0,0,,{c.upper()}")

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ass_lines) + '\n')

class AutoScriptorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        # 1. Проксирование AI запросов
        if self.path == '/api/chat':
            try:
                payload = json.loads(post_data.decode('utf-8'))
                endpoint = payload.get('endpoint')
                headers = payload.get('headers', {})
                body = payload.get('body', {})

                headers.pop('Host', None)
                headers.pop('host', None)
                headers.setdefault('User-Agent', 'AutoScriptor/1.0')

                req_data = json.dumps(body).encode('utf-8')
                req = urllib.request.Request(endpoint, data=req_data, headers=headers, method='POST')

                with urllib.request.urlopen(req, timeout=120) as resp:
                    resp_status = resp.status
                    resp_data = resp.read()
                    
                self.send_response(resp_status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(resp_data)
            except urllib.error.HTTPError as e:
                err_data = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_data)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                err_json = json.dumps({"error": {"message": str(e)}}).encode('utf-8')
                self.wfile.write(err_json)

        # 2. Генерация нейроозвучки (Edge-TTS)
        elif self.path == '/api/tts':
            try:
                payload = json.loads(post_data.decode('utf-8'))
                text = payload.get('text', '').strip()
                voice = payload.get('voice', 'ru-RU-DmitryNeural')
                rate = payload.get('rate', '+10%')

                if not text:
                    raise ValueError("Текст для озвучки пуст")

                # Очищаем сценарий от технических ремарок
                clean_text = re.sub(r'\[.*?\]', '', text)
                clean_text = re.sub(r'\(.*?\)', '', clean_text)
                clean_text = re.sub(r'#+\s*', '', clean_text)
                clean_text = clean_text.strip()

                task_id = str(uuid.uuid4())[:8]
                audio_file = f"audio_{task_id}.mp3"
                ass_file = f"sub_{task_id}.ass"

                audio_path = os.path.join(MEDIA_DIR, audio_file)
                ass_path = os.path.join(MEDIA_DIR, ass_file)

                # Вызов edge-tts CLI для генерации mp3
                cmd = [
                    sys.executable, "-m", "edge_tts",
                    "--text", clean_text,
                    "--voice", voice,
                    "--rate", rate,
                    "--write-media", audio_path
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if proc.returncode != 0:
                    raise RuntimeError(f"Edge-TTS error: {proc.stderr}")

                # Вычисляем точную длительность аудио и формируем субтитры
                duration = get_audio_duration(audio_path)
                create_subtitles(clean_text, duration, ass_path)

                res_data = {
                    "success": True,
                    "audio_id": task_id,
                    "audio_url": f"/media/{audio_file}",
                    "duration": round(duration, 1)
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res_data).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode('utf-8'))

        # 3. Рендеринг видеоролика (FFmpeg)
        elif self.path == '/api/render-video':
            try:
                payload = json.loads(post_data.decode('utf-8'))
                audio_id = payload.get('audio_id')
                style = payload.get('style', 'cyber')

                if not audio_id:
                    raise ValueError("audio_id не передан")

                audio_path = os.path.join(MEDIA_DIR, f"audio_{audio_id}.mp3")
                ass_path = os.path.join(MEDIA_DIR, f"sub_{audio_id}.ass")
                output_file = f"video_{audio_id}.mp4"
                output_path = os.path.join(MEDIA_DIR, output_file)

                if not os.path.exists(audio_path):
                    raise FileNotFoundError("Аудиофайл не найден. Сначала выполните озвучку.")

                # Выбор цвета фона
                bg_colors = {
                    "cyber": "0x0b0f19",
                    "dark": "0x09090b",
                    "neon": "0x0f172a",
                    "gaming": "0x020617"
                }
                bg_color = bg_colors.get(style, "0x0b0f19")

                # Экранирование пути к файлу субтитров для FFmpeg
                escaped_ass = ass_path.replace('\\', '/').replace(':', '\\:')
                vf_filter = f"ass='{escaped_ass}'" if os.path.exists(ass_path) else "null"

                cmd = [
                    FFMPEG_BIN, "-y",
                    "-f", "lavfi",
                    "-i", f"color=c={bg_color}:s=720x1280:r=30",
                    "-i", audio_path,
                    "-vf", vf_filter,
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-strict", "-2",
                    "-shortest",
                    output_path
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                if proc.returncode != 0:
                    raise RuntimeError(f"FFmpeg error: {proc.stderr[:300]}")

                res_data = {
                    "success": True,
                    "video_url": f"/media/{output_file}",
                    "filename": output_file
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res_data).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

def run():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("0.0.0.0", PORT), AutoScriptorHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"==================================================")
        print(f"  AutoScriptor запущен!")
        print(f"  Адрес: {url}")
        print(f"  FFmpeg: {FFMPEG_BIN}")
        print(f"  Нейроозвучка (Edge-TTS) и рендеринг видео готовы!")
        print(f"==================================================")
        print(f"Для остановки сервера нажмите Ctrl + C")
        
        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер остановлен.")
            sys.exit(0)

if __name__ == '__main__':
    run()
