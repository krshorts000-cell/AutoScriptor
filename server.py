"""
AutoScriptor Local Server
Позволяет запускать AutoScriptor локально без ограничений CORS для любых AI-провайдеров (DeepSeek, AI STAR, OpenAI, Qwen и др.).
Использует только стандартную библиотеку Python.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import webbrowser
import os
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

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
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                payload = json.loads(post_data.decode('utf-8'))
                endpoint = payload.get('endpoint')
                headers = payload.get('headers', {})
                body = payload.get('body', {})

                # Ensure headers don't have host mismatch
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
        else:
            self.send_error(404, "Endpoint not found")

def run():
    os.chdir(DIRECTORY)
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), AutoScriptorHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"==================================================")
        print(f"  AutoScriptor запущен!")
        print(f"  Адрес: {url}")
        print(f"  Локальный прокси без CORS активен на /api/chat")
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
