"""
智能监控系统 AI Agent
功能：
1. 理解用户问题，判断是否需要调用后端接口
2. 调用后端接口获取数据
3. 使用AI分析数据并给出建议
4. 回答安全知识问题
"""

import os
import json
import time
import hmac
import base64
import hashlib
import requests
import ssl
from datetime import datetime
from urllib.parse import urlencode, urlparse
from typing import Dict, List, Optional, Tuple
import locale

# 修复websocket包名冲突问题
# 按照官方示例，使用 websocket 包
try:
    import websocket
    WebSocketApp = websocket.WebSocketApp
except ImportError:
    try:
        # 如果 websocket 包不可用，尝试 websocket-client
        from websocket import WebSocketApp
        import websocket
    except ImportError:
        raise ImportError(
            "请安装 websocket-client 包:\n"
            "1. 卸载错误的包: pip uninstall websocket -y\n"
            "2. 安装正确的包: pip install websocket-client"
        )

# ==================== 配置（硬编码）====================
# 后端配置
BACKEND_BASE_URL = "http://localhost:10215/api/v1"
BACKEND_USERNAME = "root"
BACKEND_PASSWORD = "123456"

# 科大讯飞配置（硬编码）
XF_APPID = "12fcd57c"
XF_API_SECRET = "NmIwODUzZmY0OGNlMzg0ZTZmNzM3NzI1"
XF_API_KEY = "46054bfc1b0d5da22981bb1af2896c63"
# 接口地址：根据控制台显示的服务接口地址配置
# 控制台显示：wss://spark-api.xf-yun.com/v1/x1 (X1.5深度推理接口)
XF_HOST_URL = "https://spark-api.xf-yun.com/v1/x1"  # X1.5深度推理接口
# 如果使用通用对话接口，可切换为：
# XF_HOST_URL = "https://spark-api.xf-yun.com/v3.5/chat"  # 通用对话接口


class SparkDeskClient:
    """科大讯飞 Spark API 客户端"""
    
    def __init__(self, appid: str, api_key: str, api_secret: str):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host_url = XF_HOST_URL
    
    def _build_auth_url(self) -> str:
        """
        构建鉴权URL - 按照讯飞官方文档实现
        参考：https://www.xfyun.cn/doc/spark/general_url_authentication.html
        """
        # 解析URL
        parsed = urlparse(self.host_url)
        host = parsed.netloc
        path = parsed.path
        
        # 生成RFC1123格式的时间戳（使用官方推荐的方法）
        # 参考官方文档：使用 wsgiref.handlers.format_date_time
        from datetime import datetime
        from time import mktime
        from wsgiref.handlers import format_date_time
        
        cur_time = datetime.now()
        date = format_date_time(mktime(cur_time.timetuple()))
        # 生成的date格式：Fri, 05 May 2023 10:43:39 GMT
        
        # 拼接签名字符串（严格按照官方文档格式）
        tmp = f"host: {host}\n"
        tmp += f"date: {date}\n"
        tmp += f"GET {path} HTTP/1.1"
        
        # 利用hmac-sha256算法结合APISecret对tmp签名
        tmp_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            tmp.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        # 将tmp_sha进行base64编码生成signature
        signature = base64.b64encode(tmp_sha).decode(encoding='utf-8')
        
        # 拼接authorization_origin字符串
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        
        # 将authorization_origin进行base64编码，生成最终的authorization
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        
        # 构建WebSocket URL（对参数进行URL编码）
        from urllib.parse import quote
        auth_encoded = quote(authorization, safe='')
        date_encoded = quote(date, safe='')
        host_encoded = quote(host, safe='')
        
        # 构建查询字符串
        query_string = f"authorization={auth_encoded}&date={date_encoded}&host={host_encoded}"
        ws_url = f"wss://{host}{path}?{query_string}"
        
        return ws_url
    
    def chat(self, question: str, context: List[Dict] = None, max_retries: int = 3,
             on_chunk: Optional[callable] = None) -> str:
        """
        调用讯飞Spark API进行对话
        
        Args:
            question: 用户问题
            context: 对话历史上下文，格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            max_retries: 最大重试次数
        
        Returns:
            AI回复内容
        """
        if context is None:
            context = []
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                return self._chat_once(question, context, on_chunk=on_chunk)
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次尝试失败: {error_msg}")
                    print(f"等待 {2 ** attempt} 秒后重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise Exception(f"经过 {max_retries} 次重试后仍然失败: {error_msg}")
        
        return ""
    
    def _chat_once(self, question: str, context: List[Dict], on_chunk: Optional[callable] = None) -> str:
        """单次聊天尝试"""
        result_text = []
        ws_close_flag = False
        
        def on_message(ws, message):
            nonlocal ws_close_flag
            try:
                data = json.loads(message)
                code = data.get('header', {}).get('code', -1)
                
                if code != 0:
                    error_msg = data.get('header', {}).get('message', '')
                    print(f"❌ 错误码: {code}, 错误信息: {error_msg}")
                    # 如果是AppId认证错误，提供诊断信息
                    if code == 11200:
                        print("\n🔍 AppId认证失败诊断：")
                        print(f"   使用的AppId: {self.appid}")
                        print(f"   使用的APIKey: {self.api_key[:10]}...{self.api_key[-10:]}")
                        print(f"   使用的APISecret: {self.api_secret[:10]}...{self.api_secret[-10:]}")
                        print(f"   接口地址: {self.host_url}")
                        print("\n💡 请检查：")
                        print("   1. 在讯飞控制台确认AppId是否正确")
                        print("   2. 确认AppId、APIKey、APISecret来自同一个应用")
                        print("   3. 检查应用状态是否正常")
                        print("   4. 确认接口地址与AppId匹配（v1/x1接口需要X1.5应用）")
                    ws.close()
                    return
                
                # 按照官方示例解析返回内容
                choices = data.get('payload', {}).get('choices', {})
                status = choices.get('status', 0)
                
                # 获取文本内容（实时输出，提升用户体验）
                text_list = choices.get('text', [])
                for text_item in text_list:
                    content = text_item.get('content', '')
                    if content:  # 有内容时才添加
                        result_text.append(content)
                        if on_chunk:
                            try:
                                on_chunk(content)
                            except Exception as cb_err:
                                print(f"on_chunk回调错误: {cb_err}")
                        # 实时打印，让用户看到进度
                        print(content, end='', flush=True)
                
                # 判断是否结束（按照官方示例，status=2表示结束）
                if status == 2:
                    print()  # 换行
                    print("#### 关闭会话")
                    ws_close_flag = True
                    ws.close()
            except Exception as e:
                print(f"\n解析消息错误: {e}")
                ws_close_flag = True
        
        def on_error(ws, error):
            error_msg = str(error)
            print(f"WebSocket错误: {error_msg}")
            # 如果是SSL错误，提供更详细的提示
            if "SSL" in error_msg or "EOF" in error_msg or "protocol" in error_msg:
                print("提示: 这可能是SSL连接问题，正在尝试修复...")
            nonlocal ws_close_flag
            ws_close_flag = True
        
        def on_close(ws, close_status_code, close_msg):
            pass
        
        def on_open(ws):
            # 构建请求数据（按照官方示例格式）
            # 调试：打印使用的AppId
            print(f"🔑 使用AppId: {self.appid}")
            
            # 构建消息文本数组
            text_messages = []
            
            # 添加历史上下文
            for item in context:
                text_messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })
            
            # 添加当前问题
            text_messages.append({
                "role": "user",
                "content": question
            })
            
            # 按照官方示例构建请求参数
            request_data = {
                "header": {
                    "app_id": self.appid
                    # 注意：官方示例中没有 uid 字段
                },
                "parameter": {
                    "chat": {
                        "domain": "x1",  # X1.5接口必须使用 "x1"
                        "max_tokens": 32768,  # 官方示例使用32768
                        "top_k": 6,  # 官方示例包含此字段
                        "temperature": 1.2,  # 官方示例使用1.2
                        "tools": [  # 官方示例包含tools字段
                            {
                                "web_search": {
                                    "search_mode": "normal",
                                    "enable": False
                                },
                                "type": "web_search"
                            }
                        ]
                    }
                },
                "payload": {
                    "message": {
                        "text": text_messages
                    }
                }
            }
            
            # 发送请求
            ws.send(json.dumps(request_data))
        
        # 建立WebSocket连接
        auth_url = self._build_auth_url()
        
        # 配置SSL选项，解决SSL连接问题
        ssl_options = {
            "cert_reqs": ssl.CERT_NONE,  # 不验证证书
            "check_hostname": False,     # 不检查主机名
            "ssl_version": ssl.PROTOCOL_TLS,  # 使用TLS协议
        }
        
        # 按照官方示例，禁用trace
        websocket.enableTrace(False)
        
        ws = WebSocketApp(
            auth_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        # 运行WebSocket，按照官方示例使用简单的SSL配置
        try:
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            error_msg = str(e)
            print(f"WebSocket运行错误: {error_msg}")
            if "EOF" in error_msg or "protocol" in error_msg:
                raise Exception(f"SSL连接失败: {error_msg}。请检查网络连接和SSL配置。")
            ws_close_flag = True
            raise
        
        # 等待响应完成（优化超时时间）
        timeout = 60  # 增加到60秒，因为AI响应可能需要更长时间
        start_time = time.time()
        last_print_time = start_time
        
        while not ws_close_flag and (time.time() - start_time) < timeout:
            current_time = time.time()
            # 每2秒打印一次进度提示
            if current_time - last_print_time >= 2:
                elapsed = int(current_time - start_time)
                print(f"⏳ AI正在思考中... ({elapsed}秒)")
                last_print_time = current_time
            time.sleep(0.1)
        
        if not result_text:
            raise Exception("未收到AI响应，可能是连接超时或网络问题")
        
        return ''.join(result_text).strip()


class BackendClient:
    """后端API客户端"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.external_token_mode = False  # True 表示使用前端传入的用户token

    def set_token(self, token: Optional[str], external: bool = False):
        """设置token；external=True 表示来自前端用户，不自动重登"""
        self.token = token
        self.external_token_mode = external
        self.session.headers.update({"Authorization": f"Bearer {self.token}"} if token else {})

    def _authorized_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _request(self, method: str, url: str, **kwargs):
        """
        统一请求入口：自动携带token，遇到401自动重登并重试一次
        """
        headers = kwargs.pop("headers", {})
        headers.update(self._authorized_headers())
        kwargs["headers"] = headers

        resp = self.session.request(method, url, **kwargs)

        def need_relogin(r):
            try:
                data = r.json()
                msg = str(data.get("message", "")).lower()
                code = str(data.get("code", "")).lower()
                return r.status_code == 401 or "token" in msg or "token" in code or "过期" in msg
            except Exception:
                return r.status_code == 401

        # 如果token过期，尝试重登一次
        if need_relogin(resp):
            if self.external_token_mode:
                # 前端用户token过期，直接提示
                raise Exception("用户登录已过期，请重新登录")
            print("🔄 token过期/失效，尝试重新登录(内置账号)...")
            if self.login():
                headers = kwargs.pop("headers", {})
                headers.update(self._authorized_headers())
                kwargs["headers"] = headers
                resp = self.session.request(method, url, **kwargs)
            else:
                raise Exception("内置账号登录已过期，请检查后端账号密码")

        resp.raise_for_status()
        return resp
    
    def login(self) -> bool:
        """登录获取Token"""
        try:
            response = self.session.post(
                f"{self.base_url}/user/login",
                json={"userName": self.username, "password": self.password},
                timeout=5  # 减少超时时间，加快响应
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "00000":
                print(f"登录失败: {data.get('message')}")
                return False
            
            self.token = data["data"]["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ 后端登录成功")
            return True
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False
    
    def get_alarm_list(self, page_num: int = 1, page_size: int = 10, 
                      case_type: Optional[int] = None, 
                      status: Optional[int] = None,
                      warning_level: Optional[int] = None) -> Optional[Dict]:
        """获取告警列表"""
        try:
            params = {
                "pageNum": page_num,
                "pageSize": page_size
            }
            if case_type is not None:
                params["caseType"] = case_type
            if status is not None:
                params["status"] = status
            if warning_level is not None:
                params["warningLevel"] = warning_level
            
            response = self._request(
                "GET",
                f"{self.base_url}/alarm/query",
                params=params,
                timeout=10
            )
            data = response.json()
            
            if data.get("code") != "00000":
                return None
            
            return data.get("data")
        except Exception as e:
            print(f"获取告警列表失败: {e}")
            return None
    
    def get_realtime_alarm(self) -> Optional[Dict]:
        """获取实时告警统计"""
        try:
            response = self._request(
                "GET",
                f"{self.base_url}/alarm/realtime",
                timeout=5  # 减少超时时间，加快响应
            )
            data = response.json()
            
            if data.get("code") != "00000":
                return None
            
            return data.get("data")
        except Exception as e:
            print(f"获取实时告警失败: {e}")
            return None
    
    def get_monitor_list(self) -> Optional[List[Dict]]:
        """获取监控点列表"""
        try:
            response = self._request(
                "GET",
                f"{self.base_url}/monitor",
                timeout=5  # 减少超时时间，加快响应
            )
            data = response.json()
            
            if data.get("code") != "00000":
                return None
            
            return data.get("data")
        except Exception as e:
            print(f"获取监控点列表失败: {e}")
            return None
    
    def get_alarm_by_id(self, alarm_id: int) -> Optional[Dict]:
        """根据ID获取告警详情"""
        try:
            response = self.session.get(
                f"{self.base_url}/alarm/{alarm_id}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "00000":
                return None
            
            return data.get("data")
        except Exception as e:
            print(f"获取告警详情失败: {e}")
            return None


class IntelligentAgent:
    """智能Agent - 能够理解问题、调用接口、AI分析"""
    
    def __init__(self):
        self.backend = BackendClient(BACKEND_BASE_URL, BACKEND_USERNAME, BACKEND_PASSWORD)
        self.ai_client = SparkDeskClient(XF_APPID, XF_API_KEY, XF_API_SECRET)
        self.conversation_history = []  # 对话历史
        
        # 初始化：使用内置账号登录（供后台调用时使用）。如果失败不抛异常，后续可用前端token。
        try:
            self.backend.login()
        except Exception as e:
            print(f"⚠️ 内置账号登录失败，将等待前端token：{e}")
    
    def _detect_intent(self, question: str) -> Tuple[str, Dict]:
        """
        检测用户意图，判断是否需要调用后端接口
        
        Returns:
            (intent_type, params)
            intent_type: "query_alarm", "query_monitor", "query_realtime", "knowledge", "general"
        """
        question_lower = question.lower()
        
        # 告警相关关键词
        alarm_keywords = ["告警", "报警", "警报", "告警列表", "有哪些告警", "告警信息", "告警详情", 
                         "未处理告警", "已处理告警", "告警统计", "告警数量"]
        
        # 监控点相关关键词
        monitor_keywords = ["监控", "监控点", "摄像头", "监控列表", "有哪些监控", "监控设备"]
        
        # 实时统计相关关键词
        realtime_keywords = ["实时", "当前", "现在", "今日", "今天", "统计", "概览", "大屏"]
        
        # 安全知识相关关键词
        knowledge_keywords = ["如何", "怎么", "什么是", "为什么", "安全", "知识", "方法", "建议", 
                             "注意事项", "预防", "处理", "应对"]
        
        # 判断意图
        if any(keyword in question_lower for keyword in alarm_keywords):
            params = {}
            # 提取具体参数
            if "未处理" in question_lower or "未处理" in question:
                params["status"] = 0
            elif "已处理" in question_lower or "已处理" in question:
                params["status"] = 1
            
            if "高级" in question_lower or "级别" in question_lower or "严重" in question_lower:
                params["warning_level"] = 4
            
            return "query_alarm", params
        
        elif any(keyword in question_lower for keyword in monitor_keywords):
            return "query_monitor", {}
        
        elif any(keyword in question_lower for keyword in realtime_keywords):
            return "query_realtime", {}
        
        elif any(keyword in question_lower for keyword in knowledge_keywords):
            return "knowledge", {}
        
        else:
            return "general", {}
    
    def _format_alarm_data(self, alarm_data: Dict) -> str:
        """格式化告警数据为文本"""
        if not alarm_data:
            return "暂无告警数据"
        
        alarm_list = alarm_data.get("alarmList", [])
        count = alarm_data.get("count", 0)
        
        if count == 0:
            return "当前没有符合条件的告警"
        
        result = f"共找到 {count} 条告警记录：\n\n"
        
        for i, alarm in enumerate(alarm_list[:10], 1):  # 最多显示10条
            result += f"{i}. 【{alarm.get('eventName', '未知类型')}】\n"
            result += f"   监控点: {alarm.get('name', '未知')}\n"
            result += f"   区域: {alarm.get('department', '未知')}\n"
            result += f"   级别: {alarm.get('level', '未知')}级\n"
            result += f"   时间: {alarm.get('date', '未知')}\n"
            result += f"   状态: {alarm.get('deal', '未知')}\n"
            if alarm.get('content'):
                result += f"   处理内容: {alarm.get('content')}\n"
            result += "\n"
        
        if count > 10:
            result += f"... 还有 {count - 10} 条告警未显示\n"
        
        return result
    
    def _format_realtime_data(self, realtime_data: Dict) -> str:
        """格式化实时告警数据为文本"""
        if not realtime_data:
            return "暂无实时数据"
        
        result = "📊 实时告警统计：\n\n"
        
        # 总体统计
        alarm_total = realtime_data.get("alarmTotal", {})
        result += f"总告警数: {alarm_total.get('total', 0)}\n"
        result += f"今日新增: {alarm_total.get('todayNew', 0)}\n"
        result += f"较昨日变化: {alarm_total.get('dayChange', 0)}\n\n"
        
        # 按类型统计
        case_type_list = realtime_data.get("alarmCaseTypeTotalList", [])
        if case_type_list:
            result += "按类型统计：\n"
            for item in case_type_list:
                result += f"  - {item.get('caseTypeName', '未知')}: "
                result += f"今日 {item.get('todayNew', 0)} 条，总计 {item.get('total', 0)} 条\n"
        
        return result
    
    def _format_monitor_data(self, monitor_list: List[Dict]) -> str:
        """格式化监控点数据为文本"""
        if not monitor_list:
            return "暂无监控点数据"
        
        result = f"共 {len(monitor_list)} 个监控点：\n\n"
        
        for i, monitor in enumerate(monitor_list[:10], 1):  # 最多显示10个
            result += f"{i}. {monitor.get('name', '未知')}\n"
            result += f"   区域: {monitor.get('department', '未知')}\n"
            result += f"   负责人: {monitor.get('leader', '未知')}\n"
            result += f"   状态: {'运行中' if monitor.get('running') else '已停止'}\n"
            result += f"   告警次数: {monitor.get('alarmCnt', 0)}\n\n"
        
        if len(monitor_list) > 10:
            result += f"... 还有 {len(monitor_list) - 10} 个监控点未显示\n"
        
        return result
    
    def process_question(self, question: str, on_chunk: Optional[callable] = None, user_token: Optional[str] = None) -> str:
        """
        处理用户问题的主方法
        
        Args:
            question: 用户问题
        
        Returns:
            AI分析后的回答
        """
        print(f"\n🤔 用户问题: {question}")
        
        # 1. 检测意图
        intent, params = self._detect_intent(question)
        print(f"📋 检测到意图: {intent}")
        
        # 2. 如果前端提供token，则切换为用户token模式（只对本次请求生效）
        if user_token:
            self.backend.set_token(user_token, external=True)
        else:
            # 若未提供，确保仍使用内置登录态
            if not self.backend.token:
                self.backend.login()

        # 3. 根据意图调用后端接口
        backend_data = None
        data_summary = ""
        
        if intent == "query_alarm":
            print("📞 调用后端接口: 获取告警列表")
            backend_data = self.backend.get_alarm_list(**params)
            if backend_data:
                data_summary = self._format_alarm_data(backend_data)
                print(f"✅ 获取到 {backend_data.get('count', 0)} 条告警")
        
        elif intent == "query_realtime":
            print("📞 调用后端接口: 获取实时告警统计")
            backend_data = self.backend.get_realtime_alarm()
            if backend_data:
                data_summary = self._format_realtime_data(backend_data)
                print("✅ 获取到实时统计数据")
        
        elif intent == "query_monitor":
            print("📞 调用后端接口: 获取监控点列表")
            backend_data = self.backend.get_monitor_list()
            if backend_data:
                data_summary = self._format_monitor_data(backend_data)
                print(f"✅ 获取到 {len(backend_data)} 个监控点")
        
        # 4. 构建AI提示词
        system_prompt = """你是医院安全监控系统的智能助手"小智"。你的职责是：
1. 帮助用户理解监控数据和告警信息
2. 提供专业的安全知识建议
3. 分析告警数据并给出处理建议
4. 用友好、专业、简洁的语言回答问题

请用中文回答，回答要专业、准确、易懂。"""
        
        if backend_data and data_summary:
            # 有后端数据，需要AI分析
            ai_prompt = f"""{system_prompt}

用户问题：{question}

系统数据：
{data_summary}

请根据以上数据，回答用户的问题，并给出专业的分析和处理建议。"""
        else:
            # 没有后端数据，直接回答知识问题
            ai_prompt = f"""{system_prompt}

用户问题：{question}

请直接回答用户的问题。如果涉及医院安全监控相关知识，请提供专业建议。"""
        
        # 5. 调用AI分析
        print("🤖 调用AI分析...")
        try:
            ai_response = self.ai_client.chat(ai_prompt, self.conversation_history, on_chunk=on_chunk)
            print(f"✅ AI分析完成")
            
            # 保存对话历史（只保存最近5轮）
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            if len(self.conversation_history) > 10:  # 保留最近5轮对话
                self.conversation_history = self.conversation_history[-10:]
            
            return ai_response
        except Exception as e:
            print(f"❌ AI调用失败: {e}")
            # 如果AI调用失败，返回基础回答
            if backend_data:
                return f"根据系统数据：\n{data_summary}\n\n（AI分析服务暂时不可用，请查看上述数据）"
            else:
                return "抱歉，AI服务暂时不可用，请稍后再试。"
    
    def chat(self, question: str, on_chunk: Optional[callable] = None) -> str:
        """对话接口（别名）"""
        return self.process_question(question, on_chunk=on_chunk)


def main():
    """主函数 - 交互式对话"""
    print("=" * 60)
    print("🏥 智能监控系统 AI Agent")
    print("=" * 60)
    print("\n功能说明：")
    print("1. 可以询问告警信息（如：有哪些告警？未处理的告警有哪些？）")
    print("2. 可以询问监控点信息（如：有哪些监控点？）")
    print("3. 可以询问实时统计（如：当前告警统计如何？）")
    print("4. 可以询问安全知识（如：如何预防火灾？如何处理摔倒事件？）")
    print("\n输入 'exit' 或 'quit' 退出\n")
    
    try:
        agent = IntelligentAgent()
        print("✅ Agent 初始化成功\n")
    except Exception as e:
        print(f"❌ Agent 初始化失败: {e}")
        return
    
    while True:
        try:
            question = input("\n💬 请输入您的问题: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', '退出']:
                print("\n👋 再见！")
                break
            
            # 处理问题
            response = agent.process_question(question)
            
            # 显示回答
            print("\n" + "=" * 60)
            print("🤖 AI 回答:")
            print("=" * 60)
            print(response)
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 处理错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
