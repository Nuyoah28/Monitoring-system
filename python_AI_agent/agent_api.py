"""
Agent API 服务 - 提供HTTP接口供前端或其他服务调用
可以集成到Spring Boot后端，或作为独立服务运行
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from intelligent_agent import IntelligentAgent
import json
import os
import time
import traceback
import threading
from queue import SimpleQueue

app = Flask(__name__)
# 允许跨域请求
CORS(app)

# 全局Agent实例
agent = None

def _get_user_token(req, data: dict):
    """从Header或Body获取用户token（前端用户JWT）"""
    user_token = None
    auth_header = req.headers.get('Authorization')
    if auth_header:
        user_token = auth_header.replace('Bearer ', '').strip()
    if not user_token and isinstance(data, dict):
        user_token = data.get('token')
    return user_token

def init_agent():
    """初始化Agent"""
    global agent
    try:
        print("正在初始化Agent...")
        agent = IntelligentAgent()
        print("✅ Agent初始化成功")
        return True
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        traceback.print_exc()
        return False

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        "code": "00000",
        "message": "服务正常",
        "data": {
            "status": "ok",
            "agent_ready": agent is not None
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    对话接口
    
    请求体：
    {
        "question": "用户问题"
    }
    
    响应：
    {
        "code": "00000",
        "message": "请求正常",
        "data": {
            "answer": "AI回答",
            "question": "用户问题"
        }
    }
    """
    if agent is None:
        return jsonify({
            "code": "A1000",
            "message": "Agent未初始化",
            "data": None
        }), 500
    
    try:
        # 获取请求数据
        if not request.json:
            return jsonify({
                "code": "A1000",
                "message": "请求体不能为空",
                "data": None
            }), 400
        
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "code": "A1000",
                "message": "问题不能为空",
                "data": None
            }), 400
        
        # 处理问题
        print(f"\n📥 收到请求: {question}")
        start_time = time.time()
        
        # 从Header或Body获取用户token（前端用户JWT）
        user_token = _get_user_token(request, data)

        response = agent.process_question(question, user_token=user_token)
        
        elapsed = time.time() - start_time
        print(f"📤 返回回答 (耗时: {elapsed:.2f}秒): {response[:100]}...")  # 只打印前100字符
        
        return jsonify({
            "code": "00000",
            "message": "请求正常",
            "data": {
                "answer": response,
                "question": question,
                "elapsed_time": round(elapsed, 2)  # 返回耗时（秒）
            }
        })
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 处理失败: {error_msg}")
        traceback.print_exc()
        return jsonify({
            "code": "A1000",
            "message": f"处理失败: {error_msg}",
            "data": None
        }), 500

@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式对话接口（SSE - Server-Sent Events）
    实时返回AI回答的片段，提升用户体验
    """
    if agent is None:
        return jsonify({
            "code": "A1000",
            "message": "Agent未初始化",
            "data": None
        }), 500

    def generate():
        try:
            if not request.json:
                yield f"data: {json.dumps({'type': 'error', 'message': '请求体不能为空'})}\n\n"
                return

            data = request.json
            question = data.get('question', '').strip()

            if not question:
                yield f"data: {json.dumps({'type': 'error', 'message': '问题不能为空'})}\n\n"
                return

            user_token = _get_user_token(request, data)

            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'question': question})}\n\n"

            print(f"\n📥 收到流式请求: {question}")
            start_time = time.time()

            q: SimpleQueue = SimpleQueue()
            done_flag = threading.Event()
            error_flag = threading.Event()
            full_answer_parts = []

            def run_agent():
                try:
                    agent.process_question(
                        question,
                        on_chunk=lambda c: q.put(c),
                        user_token=user_token
                    )
                except Exception as e:
                    error_flag.set()
                    q.put(json.dumps({'type': 'error', 'message': str(e)}))
                finally:
                    q.put(None)  # 结束标记
                    done_flag.set()

            threading.Thread(target=run_agent, daemon=True).start()

            # 逐条发送chunk
            while True:
                chunk = q.get()
                if chunk is None:
                    break
                if isinstance(chunk, str) and chunk.startswith('{') and '"type":"error"' in chunk:
                    yield f"data: {chunk}\n\n"
                    break
                full_answer_parts.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # 发送完成信号
            elapsed = time.time() - start_time
            yield f"data: {json.dumps({'type': 'done', 'elapsed_time': round(elapsed, 2)})}\n\n"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ 流式处理失败: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/info', methods=['GET'])
def api_info():
    """API信息"""
    return jsonify({
        "code": "00000",
        "message": "请求正常",
        "data": {
            "name": "智能监控系统 AI Agent API",
            "version": "1.0.0",
            "endpoints": {
                "health": "GET /health - 健康检查",
                "chat": "POST /chat - 对话接口",
                "chat_stream": "POST /chat/stream - 对话接口（流式SSE）",
                "info": "GET /api/info - API信息"
            },
            "features": [
                "智能问答",
                "告警信息查询",
                "监控点信息查询",
                "实时统计查询",
                "安全知识问答",
                "流式输出支持"
            ]
        }
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 启动 Agent API 服务")
    print("=" * 60)
    
    if init_agent():
        print("\n📡 API接口：")
        print("  - GET  /health      - 健康检查")
        print("  - POST /chat        - 对话接口")
        print("  - GET  /api/info    - API信息")
        print("\n🌐 服务地址: http://0.0.0.0:5000")
        print("=" * 60)
        print("\n启动服务...\n")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    else:
        print("❌ Agent初始化失败，请检查配置")
        print("   请确保：")
        print("   1. 后端服务正在运行")
        print("   2. 讯飞API配置正确")
        print("   3. 网络连接正常")
