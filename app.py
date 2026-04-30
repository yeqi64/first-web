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
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>我的信息面板</title>
            <style>
                body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                .info { background: #f0f0f0; padding: 20px; border-radius: 10px; margin: 20px 0; }
                .quote { background: #e0f0e0; padding: 20px; border-radius: 10px; margin: 20px 0; }
                button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
                .loading { color: gray; }
            </style>
        </head>
        <body>
            <h1>🚀 我的信息面板</h1>
            
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
    
    def send_json_response(self, data):
        """统一的 JSON 响应方法"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_404(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')

if __name__ == '__main__':
    port = 8080
    server = HTTPServer(('0.0.0.0', port), MyHandler)
    print(f"✅ 服务已启动，访问 http://localhost:{port}")
    print(f"📍 API 接口：")
    print(f"   - 信息接口: http://localhost:{port}/api/info")
    print(f"   - 名言接口: http://localhost:{port}/api/quote")
    server.serve_forever()