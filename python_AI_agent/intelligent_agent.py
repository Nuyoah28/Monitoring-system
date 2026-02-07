"""智能监控系统 AI Agent（Tool-Calling）- 大模型决定调用接口并分析数据"""

import json
import re
import time
import hmac
import base64
import hashlib
import requests
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, quote
from typing import Dict, List, Optional, Tuple

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

BACKEND_BASE_URL = "http://localhost:10215/api/v1"
BACKEND_USERNAME = "root"
BACKEND_PASSWORD = "123456"
XF_APPID = "12fcd57c"
XF_API_SECRET = "NmIwODUzZmY0OGNlMzg0ZTZmNzM3NzI1"
XF_API_KEY = "46054bfc1b0d5da22981bb1af2896c63"
XF_HOST_URL = "https://spark-api.xf-yun.com/v1/x1"


class SparkDeskClient:
    """科大讯飞 Spark API 客户端"""
    
    def __init__(self, appid: str, api_key: str, api_secret: str):
        self.appid = appid
        self.api_key = api_key
        self.api_secret = api_secret
        self.host_url = XF_HOST_URL
    
    def _build_auth_url(self) -> str:
        from wsgiref.handlers import format_date_time
        parsed = urlparse(self.host_url)
        host, path = parsed.netloc, parsed.path
        date = format_date_time(mktime(datetime.now().timetuple()))
        tmp = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        sig = base64.b64encode(hmac.new(
            self.api_secret.encode(), tmp.encode(), hashlib.sha256
        ).digest()).decode()
        auth = base64.b64encode(f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig}"'.encode()).decode()
        qs = f"authorization={quote(auth, safe='')}&date={quote(date, safe='')}&host={quote(host, safe='')}"
        return f"wss://{host}{path}?{qs}"
    
    def chat(self, question: str, context: List[Dict] = None, max_retries: int = 3,
             on_chunk: Optional[callable] = None) -> str:
        context = context or []
        for attempt in range(max_retries):
            try:
                return self._chat_once(question, context, on_chunk=on_chunk)
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
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
                    ws.close()
                    raise Exception(f"Spark API 错误 {code}: {data.get('header', {}).get('message', '')}")
                
                choices = data.get('payload', {}).get('choices', {})
                for t in choices.get('text', []):
                    c = t.get('content', '')
                    if c:
                        result_text.append(c)
                        on_chunk and on_chunk(c)
                if choices.get('status') == 2:
                    ws_close_flag = True
                    ws.close()
            except Exception:
                ws_close_flag = True
        
        def on_error(ws, error):
            nonlocal ws_close_flag
            ws_close_flag = True
        
        def on_open(ws):
            text_messages = [{"role": i["role"], "content": i["content"]} for i in context]
            text_messages.append({"role": "user", "content": question})
            request_data = {
                "header": {"app_id": self.appid},
                "parameter": {"chat": {"domain": "x1", "max_tokens": 32768, "top_k": 6, "temperature": 1.2, "tools": [{"web_search": {"search_mode": "normal", "enable": False}, "type": "web_search"}]}},
                "payload": {
                    "message": {
                        "text": text_messages
                    }
                }
            }
            
            ws.send(json.dumps(request_data))
        
        websocket.enableTrace(False)
        
        ws = WebSocketApp(self._build_auth_url(), on_message=on_message, on_error=on_error, on_close=lambda *a: None, on_open=on_open)
        try:
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            raise Exception(f"WebSocket 连接失败: {e}")
        if not result_text:
            raise Exception("未收到AI响应，可能是连接超时或网络问题")
        
        return ''.join(result_text).strip()


class BackendClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
        self.external_token_mode = False

    def set_token(self, token: Optional[str], external: bool = False):
        self.token = token
        self.external_token_mode = external
        self.session.headers.update({"Authorization": f"Bearer {self.token}"} if token else {})

    def _authorized_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def _request(self, method: str, url: str, **kwargs):
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

        if need_relogin(resp):
            if self.external_token_mode:
                raise Exception("用户登录已过期，请重新登录")
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
        try:
            response = self.session.post(
                f"{self.base_url}/user/login",
                json={"userName": self.username, "password": self.password},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "00000":
                return False
            self.token = data["data"]["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        except Exception:
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
        except Exception:
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
        except Exception:
            return None
    
    def get_monitor_list(self) -> Optional[List[Dict]]:
        try:
            response = self._request("GET", f"{self.base_url}/monitor", timeout=5)
            data = response.json()
            
            if data.get("code") != "00000":
                return None
            
            return data.get("data")
        except Exception:
            return None
    
    def get_alarm_by_id(self, alarm_id: int) -> Optional[Dict]:
        try:
            response = self._request("GET", f"{self.base_url}/alarm/{alarm_id}", timeout=10)
            data = response.json()
            if data.get("code") != "00000":
                return None
            return data.get("data")
        except Exception:
            return None

    def get_weather_newest(self, monitor_id: int) -> Optional[Dict]:
        try:
            response = self._request("GET", f"{self.base_url}/weather/newest/{monitor_id}", timeout=10)
            data = response.json()
            if data.get("code") != "00000":
                return None
            return data.get("data")
        except Exception:
            return None

    def get_weather_history(self, monitor_id: int) -> Optional[Dict]:
        try:
            response = self._request("GET", f"{self.base_url}/weather/all/{monitor_id}", timeout=10)
            data = response.json()
            if data.get("code") != "00000":
                return None
            return data.get("data")
        except Exception:
            return None


TOOLS_SCHEMA = {
    "tools": [
        {
            "name": "get_alarm_list",
            "description": "获取告警列表。当用户询问告警、报警、警报、未处理告警、已处理告警、告警列表、告警统计、告警数量等信息时调用。",
            "parameters": {
                "status": "int|null，0=未处理，1=已处理，null=不筛选",
                "warning_level": "int|null，4=高级/严重，null=不筛选",
                "page_num": "int，页码，默认1",
                "page_size": "int，每页数量，默认10"
            }
        },
        {
            "name": "get_realtime_alarm",
            "description": "获取实时告警统计。当用户询问当前、今日、今天、实时、统计、概览、大屏、整体情况时调用。",
            "parameters": {}
        },
        {
            "name": "get_monitor_list",
            "description": "获取监控点列表。当用户询问监控点、摄像头、监控设备、有哪些监控、监控列表时调用。",
            "parameters": {}
        },
        {
            "name": "get_alarm_detail",
            "description": "根据告警ID获取详情。当用户明确提到某个告警的ID或编号（如：ID为123的告警、告警123详情）时调用。",
            "parameters": {
                "alarm_id": "int，告警ID"
            }
        },
        {
            "name": "get_weather_newest",
            "description": "获取指定监控点的最新天气。当用户询问某监控点的天气、气温、湿度、当前天气、最新天气时调用。",
            "parameters": {
                "monitor_id": "int，监控点ID"
            }
        },
        {
            "name": "get_weather_history",
            "description": "获取指定监控点的天气历史。当用户询问某监控点的天气记录、历史天气、天气变化趋势时调用。",
            "parameters": {
                "monitor_id": "int，监控点ID"
            }
        }
    ]
}

TOOL_SELECTION_PROMPT = """你是医院安全监控助手。根据用户问题，输出 JSON（仅 JSON）：
- 需调多个接口：[{{"tool":"工具名","params":{{...}}}}, {{"tool":"工具名2","params":{{...}}}}]
- 只需一个：{{"tool":"工具名","params":{{...}}}}
- 不需调：{{"tool":"none","params":{{}}}}

用户可能一次问多个问题，需调用多个接口。例如："告警数量和1号监控温度" 需调用 get_alarm_list 和 get_weather_newest。

工具：{tools_desc}

用户：{question}

输出："""


class IntelligentAgent:
    def __init__(self):
        self.backend = BackendClient(BACKEND_BASE_URL, BACKEND_USERNAME, BACKEND_PASSWORD)
        self.ai_client = SparkDeskClient(XF_APPID, XF_API_KEY, XF_API_SECRET)
        self.conversation_history = []
        self.backend.login()
    
    def _get_tools_desc(self) -> str:
        lines = []
        for t in TOOLS_SCHEMA["tools"]:
            lines.append(f"- **{t['name']}**: {t['description']}")
            if t.get("parameters"):
                for k, v in t["parameters"].items():
                    lines.append(f"    - {k}: {v}")
        return "\n".join(lines)
    
    def _parse_tool_calls(self, llm_output: str) -> List[Tuple[str, Dict]]:
        """解析 LLM 输出，返回 [(tool_name, params), ...]，支持多工具"""
        llm_output = llm_output.strip()
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', llm_output)
        if json_match:
            llm_output = json_match.group(1).strip()
        obj_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', llm_output)
        if obj_match:
            try:
                obj = json.loads(obj_match.group())
                result = []
                items = obj if isinstance(obj, list) else [obj]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    tool = item.get("tool", "none")
                    params = item.get("params", {}) or {}
                    if tool and tool != "none":
                        result.append((tool, params if isinstance(params, dict) else {}))
                if result:
                    return result
            except json.JSONDecodeError:
                pass
        return []
    
    def _execute_tool(self, tool_name: str, params: Dict) -> Optional[str]:
        """
        执行指定工具，返回格式化后的数据文本
        """
        if tool_name == "get_alarm_list":
            backend_data = self.backend.get_alarm_list(
                page_num=params.get("page_num", 1),
                page_size=params.get("page_size", 10),
                status=params.get("status") if "status" in params else None,
                warning_level=params.get("warning_level") if "warning_level" in params else None
            )
            return self._format_alarm_data(backend_data) if backend_data else "暂无告警数据"
        
        elif tool_name == "get_realtime_alarm":
            backend_data = self.backend.get_realtime_alarm()
            return self._format_realtime_data(backend_data) if backend_data else "暂无实时数据"
        
        elif tool_name == "get_monitor_list":
            backend_data = self.backend.get_monitor_list()
            return self._format_monitor_data(backend_data) if backend_data else "暂无监控点数据"
        
        elif tool_name == "get_alarm_detail":
            alarm_id = params.get("alarm_id")
            if alarm_id is None:
                return "缺少告警ID参数"
            try:
                alarm_id = int(alarm_id)
            except (TypeError, ValueError):
                return "告警ID必须为数字"
            backend_data = self.backend.get_alarm_by_id(alarm_id)
            if backend_data:
                return self._format_alarm_data({"alarmList": [backend_data], "count": 1})
            return f"未找到ID为 {alarm_id} 的告警"
        elif tool_name == "get_weather_newest":
            mid = params.get("monitor_id")
            if mid is None:
                return "缺少监控点ID参数"
            try:
                mid = int(mid)
            except (TypeError, ValueError):
                return "监控点ID必须为数字"
            data = self.backend.get_weather_newest(mid)
            return self._format_weather_data(data, single=True) if data else f"监控点 {mid} 暂无天气数据"
        elif tool_name == "get_weather_history":
            mid = params.get("monitor_id")
            if mid is None:
                return "缺少监控点ID参数"
            try:
                mid = int(mid)
            except (TypeError, ValueError):
                return "监控点ID必须为数字"
            data = self.backend.get_weather_history(mid)
            return self._format_weather_data(data, single=False) if data else f"监控点 {mid} 暂无天气历史"
        return None
    
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
    
    def _format_weather_data(self, data, single: bool = True) -> str:
        if single:
            items = [data] if isinstance(data, dict) else []
        else:
            items = data if isinstance(data, list) else (data.get("list") or data.get("records") or []) if isinstance(data, dict) else []
        if not items:
            return "暂无天气数据"
        result = "最新天气：\n\n" if single else f"共 {len(items)} 条天气记录：\n\n"
        for i, w in enumerate(items[:15], 1):
            result += f"{i}. 温度 {w.get('temperature', '未知')}℃ 湿度 {w.get('humidity', '未知')}% 天气 {w.get('weather', '未知')}"
            if w.get("createTime") or w.get("date") or w.get("time"):
                result += f" 时间 {w.get('createTime') or w.get('date') or w.get('time', '未知')}"
            result += "\n"
        if len(items) > 15:
            result += f"... 还有 {len(items) - 15} 条未显示\n"
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
        处理用户问题的主方法（Tool-Calling 流程）
        
        Args:
            question: 用户问题
        
        Returns:
            AI分析后的回答
        """
        print(f"\n🤔 用户问题: {question}")
        
        # 1. 如果前端提供token，则切换为用户token模式
        if user_token:
            self.backend.set_token(user_token, external=True)
        else:
            if not self.backend.token:
                self.backend.login()

        # 2. 由大模型决定调用哪个工具（Tool-Calling 第一步）
        tools_desc = self._get_tools_desc()
        tool_prompt = TOOL_SELECTION_PROMPT.format(tools_desc=tools_desc, question=question)
        
        print("🔍 大模型分析意图中...")
        try:
            tool_selection_response = self.ai_client.chat(
                tool_prompt,
                context=[],
                on_chunk=None
            )
        except Exception as e:
            print(f"❌ 意图分析失败: {e}，将直接回答（不调用接口）")
            tool_selection_response = '{"tool": "none", "params": {}}'
        
        tool_calls = self._parse_tool_calls(tool_selection_response)
        parts = []
        for tool_name, tool_params in tool_calls:
            r = self._execute_tool(tool_name, tool_params)
            if r:
                parts.append(f"【{tool_name}】\n{r}")
        data_summary = "\n\n".join(parts) if parts else ""
        
        # 4. 构建AI提示词（Tool-Calling 第二步：根据数据生成回答）
        system_prompt = """你是医院安全监控系统的智能助手"小智"。你的职责是：
1. 帮助用户理解监控数据和告警信息
2. 提供专业的安全知识建议
3. 分析告警数据并给出处理建议
4. 用友好、专业、简洁的语言回答问题

请用中文回答，回答要专业、准确、易懂。"""
        
        if data_summary:
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
            if data_summary:
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
    print("\n功能说明（Tool-Calling：由大模型自动判断调用哪些接口）：")
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
