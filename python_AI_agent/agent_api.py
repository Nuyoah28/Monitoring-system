"""
Agent API 服务 - 提供HTTP接口供前端或其他服务调用
可以集成到Spring Boot后端，或作为独立服务运行
"""

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_sock import Sock
from intelligent_agent import IntelligentAgent
import json
import os
import time
import traceback
import threading
import uuid
from queue import SimpleQueue
app = Flask(__name__)
# 长文本 TTS 音频缓存：id -> mp3_bytes，POST 生成后通过短 URL 播放，避免 GET 长度限制
_tts_audio_cache = {}
_tts_cache_lock = threading.Lock()
sock = Sock(app)
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
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/chat/voice', methods=['POST'])
def chat_voice():
    """
    语音对话接口：上传音频(WAV) -> 识别为文字 -> Agent 回答 -> 可选返回 TTS 音频
    
    请求方式一：multipart/form-data，字段 audio 为 WAV 文件
    请求方式二：JSON  body: { "audio_base64": "base64编码的WAV", "return_tts": true }
    
    响应：{ "code", "message", "data": { "question", "answer", "audio_base64"? } }
    """
    if agent is None:
        return jsonify({"code": "A1000", "message": "Agent未初始化", "data": None}), 500

    import base64
    audio_bytes = None
    return_tts = False
    user_token = None

    if request.content_type and 'multipart/form-data' in request.content_type:
        f = request.files.get('audio')
        if not f:
            return jsonify({"code": "A1000", "message": "请上传 audio 文件", "data": None}), 400
        audio_bytes = f.read()
        return_tts = request.form.get('return_tts', 'false').lower() == 'true'
    elif request.json:
        data = request.json
        b64 = data.get('audio_base64')
        if not b64:
            return jsonify({"code": "A1000", "message": "请提供 audio_base64", "data": None}), 400
        try:
            audio_bytes = base64.b64decode(b64)
        except Exception as e:
            return jsonify({"code": "A1000", "message": f"base64 解码失败: {e}", "data": None}), 400
        return_tts = data.get('return_tts', False)
        user_token = _get_user_token(request, data)
    else:
        return jsonify({"code": "A1000", "message": "请使用 multipart 或 JSON 提交音频", "data": None}), 400

    try:
        from voice_utils import stt_from_bytes, tts_to_bytes
    except ImportError:
        return jsonify({"code": "A1000", "message": "语音模块未安装: pip install SpeechRecognition edge-tts", "data": None}), 500

    ok, question = stt_from_bytes(audio_bytes)
    if not ok:
        return jsonify({"code": "A1000", "message": question or "语音识别失败", "data": None}), 400
    if not question.strip():
        return jsonify({"code": "A1000", "message": "未识别到有效语音", "data": None}), 400

    response = agent.process_question(question.strip(), user_token=user_token)
    result_data = {"question": question.strip(), "answer": response}

    if return_tts and response:
        ok_tts, mp3_bytes, err = tts_to_bytes(response)
        if ok_tts and mp3_bytes:
            result_data["audio_base64"] = base64.b64encode(mp3_bytes).decode('utf-8')
            result_data["audio_content_type"] = "audio/mpeg"

    return jsonify({
        "code": "00000",
        "message": "请求正常",
        "data": result_data
    })


@app.route('/tts', methods=['GET', 'POST'])
def tts():
    """
    语音合成：传入文本，返回 MP3 base64。用于文字回复的语音播放。
    GET: ?text=xxx  或  POST JSON: { "text": "xxx" }
    响应: { "code": "00000", "data": { "audio_base64": "...", "audio_content_type": "audio/mpeg" } }
    """
    import base64
    text = ""
    if request.method == 'GET':
        text = (request.args.get('text') or "").strip()
    else:
        if request.json:
            text = (request.json.get('text') or "").strip()
    if not text:
        return jsonify({"code": "A1000", "message": "请提供 text 参数", "data": None}), 400
    try:
        from voice_utils import tts_to_bytes
    except ImportError:
        return jsonify({"code": "A1000", "message": "语音模块未安装", "data": None}), 500
    ok_tts, mp3_bytes, err = tts_to_bytes(text)
    if not ok_tts or not mp3_bytes:
        return jsonify({"code": "A1000", "message": err or "TTS 合成失败", "data": None}), 500
    return jsonify({
        "code": "00000",
        "message": "请求正常",
        "data": {
            "audio_base64": base64.b64encode(mp3_bytes).decode("utf-8"),
            "audio_content_type": "audio/mpeg"
        }
    })


@app.route('/tts/audio', methods=['GET', 'POST'])
def tts_audio():
    """
    语音合成。GET: ?text=xxx（短文本，URL 有长度限制）。
    POST: body {"text": "..."} -> 返回 {"play_url": "http://host/tts/audio/stream/<id>"}，用该 URL 播放可支持长文本。
    """
    text = ""
    if request.method == 'POST' and request.json:
        text = (request.json.get('text') or "").strip()
    else:
        text = (request.args.get('text') or "").strip()
    if not text:
        return jsonify({"code": "A1000", "message": "请提供 text 参数", "data": None}), 400
    try:
        from voice_utils import tts_to_bytes
    except ImportError:
        return jsonify({"code": "A1000", "message": "语音模块未安装", "data": None}), 500
    ok_tts, mp3_bytes, err = tts_to_bytes(text)
    if not ok_tts or not mp3_bytes:
        return jsonify({"code": "A1000", "message": err or "TTS 合成失败", "data": None}), 500

    if request.method == 'POST':
        # 长文本：存入缓存，返回短 URL，避免 GET 长度限制导致念不完
        sid = str(uuid.uuid4())
        with _tts_cache_lock:
            _tts_audio_cache[sid] = mp3_bytes
        base_url = request.host_url.rstrip('/')
        play_url = f"{base_url}/tts/audio/stream/{sid}"
        return jsonify({
            "code": "00000",
            "message": "请求正常",
            "data": {"play_url": play_url}
        })

    from flask import Response
    return Response(mp3_bytes, mimetype="audio/mpeg", headers={"Content-Disposition": "inline; filename=tts.mp3"})


@app.route('/tts/audio/stream/<sid>', methods=['GET'])
def tts_audio_stream(sid):
    """根据 POST /tts/audio 返回的 play_url 拉取音频流，播放后即从缓存删除。"""
    with _tts_cache_lock:
        mp3_bytes = _tts_audio_cache.pop(sid, None)
    if not mp3_bytes:
        return jsonify({"code": "A1000", "message": "音频已过期或不存在", "data": None}), 404
    from flask import Response
    return Response(mp3_bytes, mimetype="audio/mpeg", headers={"Content-Disposition": "inline; filename=tts.mp3"})


@sock.route('/api/v1/gpt/ws/<token>')
def gpt_ws(ws, token):
    """
    WebSocket对话接口 (适配Uniapp端)
    """
    print(f"🔗 WebSocket连接建立 (Token: {token})")
    
    try:
        while True:
            # 接收消息
            message = ws.receive()
            if not message:
                break
                
            print(f"📥 收到WebSocket消息: {message}")
            
            try:
                # 尝试解析JSON
                # Uniapp端发送的是 JSON.stringify(ask) -> "\"问题\""
                data = json.loads(message)
                if isinstance(data, dict):
                    question = data.get('question', '') or data.get('content', '')
                else:
                    question = str(data)
            except:
                question = message
            
            question = question.strip()
            if not question:
                continue
                
            print(f"❓ 处理问题: {question}")
            
            try:
                if agent:
                    # 使用Agent处理，并通过回调发送chunk
                    agent.process_question(
                        question, 
                        on_chunk=lambda c: ws.send(c)
                    )
                else:
                    ws.send("⚠️ Agent未初始化")
            except Exception as e:
                error_msg = f"❌ 处理出错: {str(e)}"
                print(error_msg)
                ws.send(error_msg)
            
            # 发送结束标记 (Home.vue line 94: if(res.data !== "[DONE]"))
            ws.send("[DONE]")
            
    except Exception as e:
        print(f"❌ WebSocket异常: {e}")
    finally:
        print("🔗 WebSocket连接关闭")

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
                "chat_voice": "POST /chat/voice - 语音对话（上传 WAV，可选返回 TTS 音频）",
                "info": "GET /api/info - API信息"
            },
            "features": [
                "智能问答",
                "告警信息查询",
                "监控点信息查询",
                "实时统计查询",
                "安全知识问答",
                "流式输出支持",
                "语音输入/输出（STT+TTS）"
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
        print("  - POST /chat/voice   - 语音对话（WAV 上传，可选 TTS）")
        print("  - GET  /api/info    - API信息")
        print("\n🌐 服务地址: http://0.0.0.0:5050")
        print("=" * 60)
        print("\n启动服务...\n")
        app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)
    else:
        print("❌ Agent初始化失败，请检查配置")
        print("   请确保：")
        print("   1. 后端服务正在运行")
        print("   2. 讯飞API配置正确")
        print("   3. 网络连接正常")
