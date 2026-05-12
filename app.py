#!/usr/bin/env python3
"""
带 API 的 Web 服务
- 返回 HTML 页面（前端负责展示）
- 提供 /api/info 接口（返回时间、IP）
- 提供 /api/quote 接口（返回随机名言）
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json
import urllib.request
import urllib.parse
from urllib.parse import parse_qs  
import socket
import sqlite3


#  数据库操作
def init_database():
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_all_messages():
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nickname, content, created_at FROM messages ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_message(nickname, content):
    conn = sqlite3.connect('messages.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (nickname, content) VALUES (?, ?)', (nickname, content))
    conn.commit()
    conn.close()

#  辅助函数
def escape_html(text):
#   HTML 转义函数（防止 XSS 攻击）
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_post_data(post_str):
    parsed = parse_qs(post_str)
    return {key: value[0] for key, value in parsed.items()}

def get_local_ip():
    """获取本机局域网 IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'

# HTTP请求处理器

class MyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        # 路由：根据不同的路径，做不同的事
        if self.path == '/':
            self.handle_html()
        elif self.path == '/api/info':
            self.handle_api_info()
        elif self.path == '/api/quote':
            self.handle_api_quote()
        else:
            self.send_404()
    
    def handle_html(self):
        """返回主页面 HTML（前端代码）"""
        messages = get_all_messages()
    
        # 构建留言列表的 HTML
        messages_html = '<div class="messages">'
        for nickname, content, created_at in messages:
            messages_html += f'''
                <div class="message">
                    <strong>{escape_html(nickname)}</strong> 说：
                    <p>{escape_html(content)}</p>
                    <small>{created_at}</small>
                </div>
            '''
        messages_html += '</div>'
    

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>留言板</title>
            <style>
                body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                .info { background: #f0f0f0; padding: 20px; border-radius: 10px; margin: 20px 0; }
                .quote { background: #e0f0e0; padding: 20px; border-radius: 10px; margin: 20px 0; }
                button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
                .loading { color: gray; }
                .message {{ border-bottom: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
                textarea {{ width: 100%; height: 80px; }}
                input[type=text] {{ width: 200px; }}
            </style>
        </head>
        <body>
            <h1>🚀 留言板</h1>
            
            {messages_html}
        
            <h2>发表留言</h2>
            <form method="POST" action="/api/message">
                <input type="text" name="nickname" placeholder="你的昵称" required>
                <textarea name="content" placeholder="留言内容" required></textarea>
                <button type="submit">提交留言</button>
            </form>

            <div class="info" id="infoArea">
                <p>加载中...</p>
            </div>
            
            <div class="quote" id="quoteArea">
                <p>点击按钮获取每日一言</p>
            </div>
            
            <button onclick="loadQuote()">✨ 随机一言</button>
            
            <script>
                // 页面加载时自动获取信息
                loadInfo();
                
                function loadInfo() {
                    fetch('/api/info')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('infoArea').innerHTML = `
                                <p>⏰ 服务器时间：${data.time}</p>
                                <p>🌐 你的 IP：${data.client_ip}</p>
                                <p>📡 服务器 IP：${data.server_ip}</p>
                            `;
                        });
                }
                
                function loadQuote() {
                    const quoteDiv = document.getElementById('quoteArea');
                    quoteDiv.innerHTML = '<p class="loading">加载中...</p>';
                    
                    fetch('/api/quote')
                        .then(response => response.json())
                        .then(data => {
                            quoteDiv.innerHTML = `
                                <p>📖 "${data.quote}"</p>
                                <p>—— ${data.source || '未知出处'}</p>
                            `;
                        });
                }
            </script>
        </body>
        </html>
        """

        # 替换占位符
        html = html_template.replace('{messages_html}', messages_html)

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_api_info(self):
        """返回服务器信息和客户端信息"""
        # 获取客户端 IP
        client_ip = self.client_address[0]
        # 获取服务器 IP（简单方法）
        server_ip = self.server.server_address[0]
        
        data = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'client_ip': client_ip,
            'server_ip': server_ip
        }
        
        self.send_json_response(data)
    

    def handle_api_quote(self):
        """调用第三方 API 获取名言"""
        try:
            # 调用免费的公开 API（hitokoto.cn - 一言）
            url = 'https://v1.hitokoto.cn/'
            with urllib.request.urlopen(url, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                quote = result.get('hitokoto', '今天也要加油！')
                source = result.get('from', '未知')
        except Exception as e:
            # 如果 API 调用失败，返回备用内容
            quote = "代码如诗，万物互联。"
            source = "你的工程师"
        
        self.send_json_response({'quote': quote, 'source': source})
    
    def do_POST(self):
        if self.path == '/api/message':
            self.handle_post_message()
        else:
            self.send_404()

    def handle_post_message(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        post_str = post_data.decode('utf-8')
        params = parse_post_data(post_str)
    
        nickname = params.get('nickname', '')
        content = params.get('content', '')
    
        if nickname and content:
            save_message(nickname, content)
    
        self.send_redirect('/')

 # 通用响应方法
    def send_json_response(self, data):
        """统一的 JSON 响应方法"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_redirect(self, location):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def handle_one_request(self):
        # 设置每个请求的最大处理时间为 30 秒
        self.connection.settimeout(30)
        try:
            super().handle_one_request()
        except socket.timeout:
            print("请求处理超时，已自动断开")


if __name__ == '__main__':
    init_database()
    port = 8080
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    print(f"✅ 服务已启动，访问 http://localhost:{port}")
    print(f"📍 API 接口：")
    print(f"   - 信息接口: http://localhost:{port}/api/info")
    print(f"   - 名言接口: http://localhost:{port}/api/quote")
    server.serve_forever()
