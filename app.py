#!/usr/bin/env python3
from http.server import HTTPServer,BaseHTTPRequestHandler
from datetime import datetime
class SimpleHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		html_content = f"""
		<!DOCTYPE html>
		<html>
		<head>
			<title>我的第一个Web服务</title>
			<meta charset="utf-8">
		</head>
		<body>
			<h1>Hello World!</h1>
			<p>这是在ThinkPad L410 上的 Python Web 服务</p>
			<p>当前时间：{current_time}</p>
			<p>你访问的路径： {self.path}</p>
		</body>
		</html>
		"""
		
		self.send_response(200)
		self.send_header('Content-type','text/html;charset=utf-8')
		self.end_headers()
		self.wfile.write(html_content.encode('utf-8'))

	def log_message(self, format, *args):
		print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")
if __name__ == '__main__':
	port = 8080
	server = HTTPServer(('0.0.0.0', port), SimpleHandler)
	print(f"Web服务已启动")
	print(f"本地访问：http://localhost:{port}")
	print(f"局域网访问:http://你的局域网IP:{port}")
	print(f"查看局域网IP的命令：hostname -I")
	print(f"按 Ctrl+C 停止服务")

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print("/n 服务已停止")
		server.shutdown()
