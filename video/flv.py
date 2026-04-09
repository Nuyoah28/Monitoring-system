import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import threading
import webbrowser
import argparse


def create_flv_server(port=8848, directory=None):
    """
    创建HTTP服务器提供FLV文件访问

    Args:
        port: 端口号，默认8848
        directory: 文件目录，默认为当前目录
    """
    if directory is None:
        directory = os.getcwd()

    # 切换到指定目录
    os.chdir(directory)

    # 创建自定义处理程序，设置正确的MIME类型和CORS头部
    class FLVRequestHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            # 设置CORS头部，允许跨域访问
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.send_header('Access-Control-Max-Age', '86400')

            # 为.flv文件设置正确的MIME类型
            if self.path.endswith('.flv'):
                self.send_header('Content-Type', 'video/x-flv')
            elif self.path.endswith('.mp4'):
                self.send_header('Content-Type', 'video/mp4')
            elif self.path.endswith('.m3u8'):
                self.send_header('Content-Type', 'application/x-mpegURL')
            elif self.path.endswith('.ts'):
                self.send_header('Content-Type', 'video/MP2T')

            SimpleHTTPRequestHandler.end_headers(self)

        def do_OPTIONS(self):
            """处理OPTIONS预检请求"""
            self.send_response(200, "OK")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.send_header('Access-Control-Max-Age', '86400')
            self.end_headers()

        def do_GET(self):
            """处理GET请求，添加Range请求支持（用于视频流）"""
            # 检查是否是范围请求
            if 'Range' in self.headers:
                return self.handle_range_request()

            # 否则调用父类的GET处理
            return SimpleHTTPRequestHandler.do_GET(self)

        def handle_range_request(self):
            """处理HTTP Range请求，支持视频流播放"""
            try:
                # 获取文件路径
                path = self.translate_path(self.path)
                if not os.path.exists(path):
                    self.send_error(404, "File not found")
                    return

                # 获取文件大小
                fsize = os.path.getsize(path)

                # 解析Range头部
                range_header = self.headers.get('Range')
                if not range_header or not range_header.startswith('bytes='):
                    self.send_error(400, "Invalid Range header")
                    return

                # 解析范围
                range_str = range_header[6:]
                if '-' in range_str:
                    start_str, end_str = range_str.split('-', 1)
                    start = int(start_str) if start_str else 0
                    end = int(end_str) if end_str else fsize - 1
                else:
                    self.send_error(400, "Invalid Range format")
                    return

                # 验证范围
                if start >= fsize or end >= fsize or start > end:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    return

                # 计算实际读取的字节数
                length = end - start + 1

                # 发送206 Partial Content响应
                self.send_response(206)
                self.send_header('Content-Type', self.guess_type(path))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Range', f'bytes {start}-{end}/{fsize}')
                self.send_header('Content-Length', str(length))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Expose-Headers', 'Content-Range, Content-Length')
                self.end_headers()

                # 发送文件内容
                with open(path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        self.wfile.write(data)
                        remaining -= len(data)

            except Exception as e:
                self.send_error(500, f"Internal server error: {str(e)}")

        def log_message(self, format, *args):
            # 自定义日志格式，减少控制台输出
            print(f"[{self.log_date_time_string()}] {format % args}")

    # 创建服务器
    with socketserver.TCPServer(("", port), FLVRequestHandler) as httpd:
        print(f"服务器启动在端口 {port}")
        print(f"文件目录: {directory}")
        print(f"访问地址: http://localhost:{port}/")
        print(f"网络地址: http://{get_local_ip()}:{port}/")
        print("\n可用文件:")
        for file in get_video_files(directory):
            print(f"  http://localhost:{port}/{file}")
        print("\n按 Ctrl+C 停止服务器")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")


def get_local_ip():
    """获取本地IP地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_video_files(directory):
    """获取目录中的所有视频文件"""
    video_extensions = {'.flv', '.mp4', '.m3u8', '.ts', '.mkv', '.avi', '.mov', '.wmv', '.webm'}
    video_files = []
    for file in os.listdir(directory):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in video_extensions):
            video_files.append(file)
    return video_files


def start_server_in_thread(port, directory):
    """在新线程中启动服务器"""
    server_thread = threading.Thread(
        target=create_flv_server,
        args=(port, directory),
        daemon=True
    )
    server_thread.start()
    return server_thread


def main():
    parser = argparse.ArgumentParser(description='启动HTTP服务器提供视频文件访问（支持跨域）')
    parser.add_argument('--port', '-p', type=int, default=8848,
                        help='端口号 (默认: 8848)')
    parser.add_argument('--dir', '-d', type=str, default=None,
                        help='文件目录 (默认: 当前目录)')
    parser.add_argument('--browser', '-b', action='store_true',
                        help='启动后自动打开浏览器')
    parser.add_argument('--cors', '-c', action='store_true', default=True,
                        help='启用CORS跨域支持 (默认: 启用)')
    parser.add_argument('--range', '-r', action='store_true', default=True,
                        help='启用Range请求支持 (默认: 启用)')

    args = parser.parse_args()

    # 如果指定了目录，检查是否存在
    if args.dir and not os.path.isdir(args.dir):
        print(f"错误: 目录 '{args.dir}' 不存在")
        sys.exit(1)

    # 获取实际目录
    directory = args.dir if args.dir else os.getcwd()

    # 显示启动信息
    print("=" * 50)
    print("视频文件HTTP服务器 (支持跨域和Range请求)")
    print("=" * 50)
    print(f"CORS支持: {'已启用' if args.cors else '已禁用'}")
    print(f"Range请求支持: {'已启用' if args.range else '已禁用'}")
    print("=" * 50)

    # 启动服务器
    create_flv_server(args.port, directory)


if __name__ == "__main__":
    main()