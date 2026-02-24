"""
Agent 语音功能：语音识别(STT) + 语音合成(TTS)
- STT: 麦克风/音频文件 -> 文字 (speech_recognition，默认 Google 免费)
- TTS: 文字 -> 播放/保存音频 (edge-tts，免费中文)
依赖: pip install SpeechRecognition edge-tts
可选录音: pip install pyaudio 或 pip install sounddevice
"""

import re
from typing import Optional, Tuple


# 常见表情/符号的 Unicode 范围，TTS 前去掉避免读出
_EMOJI_AND_SYMBOL_PATTERN = re.compile(
    "["
    "\u2600-\u26FF"  # 杂项符号
    "\u2700-\u27BF"  # 丁巴特
    "\uFE00-\uFE0F"  # 变体选择符
    "\U0001F300-\U0001F9FF"  # 表情、符号等
    "\U0001F600-\U0001F64F"  # 表情
    "\U0001F680-\U0001F6FF"  # 交通等
    "\U0001F1E0-\U0001F1FF"  # 旗帜
    "]+",
    re.UNICODE,
)


def strip_markdown_for_tts(text: str) -> str:
    """
    将 Markdown 转为纯文本，供 TTS 朗读，去掉星号、井号、表情等无关符号。
    """
    if not text or not text.strip():
        return text
    t = text.strip()
    # 代码块：去掉 ```...``` 及其内容或只保留内部文字
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`[^`]+`", lambda m: m.group(0)[1:-1], t)
    # 标题：去掉 # ## ### 等
    t = re.sub(r"^#+\s*", "", t, flags=re.MULTILINE)
    # 粗体/斜体：去掉 ** __ * _
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"_([^_]+)_", r"\1", t)
    # 链接：[文字](url) -> 文字
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]", r"\1", t)
    # 列表：去掉 - * 数字. 等行首符号
    t = re.sub(r"^[\s]*[-*•]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^[\s]*\d+\.\s+", "", t, flags=re.MULTILINE)
    # 去掉残留的 Markdown/格式符号（星号、下划线、反引号、井号等，单独或连续）
    t = re.sub(r"[*_`#]+", " ", t)
    # 去掉表格等残留的 | 以及 > 引用符
    t = re.sub(r"\s*[|>]\s*", " ", t)
    # 去掉表情符号和常见装饰符号
    t = _EMOJI_AND_SYMBOL_PATTERN.sub("", t)
    # 多余空白与换行
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" +", " ", t)
    return t.strip()


# ---------------------------------------------------------------------------
# 语音识别 (STT)
# ---------------------------------------------------------------------------

def stt_from_file(audio_path: str, language: str = "zh-CN") -> Tuple[bool, str]:
    """
    从音频文件识别文字。
    返回 (成功, 文本)，失败时文本为错误说明。
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return False, "请安装: pip install SpeechRecognition"

    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
    except Exception as e:
        return False, f"读取音频失败: {e}"

    return _recognize(r, audio, language)


def _ensure_wav_bytes(audio_bytes: bytes) -> bytes:
    """若非 WAV 格式（如 mp3），尝试转为 WAV 再识别。"""
    if len(audio_bytes) >= 4 and audio_bytes[:4] == b"RIFF":
        return audio_bytes
    try:
        from pydub import AudioSegment
        import io
        buf = io.BytesIO(audio_bytes)
        # 常见非 WAV：mp3（ID3 或 0xFF 0xFB）、m4a 等
        fmt = "mp3" if (audio_bytes[:3] == b"ID3" or (len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0)) else None
        seg = AudioSegment.from_file(buf, format=fmt)
        out = io.BytesIO()
        seg.export(out, format="wav")
        return out.getvalue()
    except Exception:
        return audio_bytes


def stt_from_bytes(audio_bytes: bytes, language: str = "zh-CN") -> Tuple[bool, str]:
    """从音频字节识别文字（支持 WAV；mp3 等会先转为 WAV）。"""
    try:
        import speech_recognition as sr
    except ImportError:
        return False, "请安装: pip install SpeechRecognition"

    audio_bytes = _ensure_wav_bytes(audio_bytes)
    r = sr.Recognizer()
    try:
        import io
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = r.record(source)
    except Exception as e:
        return False, f"读取音频失败: {e}"

    return _recognize(r, audio, language)


def _recognize(recognizer, audio, language: str) -> Tuple[bool, str]:
    """内部：调用识别引擎。优先 Google 免费，可扩展讯飞等。"""
    # Google 免费（无需 key，有网络即可）
    try:
        text = recognizer.recognize_google(audio, language=language)
        return True, (text or "").strip()
    except Exception as e:
        err = str(e).lower()
        if "connection" in err or "network" in err:
            return False, "网络不可用，请检查后重试"
        if "not understand" in err or "recognition" in err:
            return False, "未识别到有效语音"
        return False, f"识别失败: {e}"


def record_audio(seconds: int = 5, sample_rate: int = 16000) -> Tuple[bool, Optional[bytes], str]:
    """
    从麦克风录制指定秒数，返回 WAV 字节。
    返回 (成功, wav_bytes 或 None, 错误信息)。
    """
    try:
        import sounddevice as sd
        import numpy as np
        import io
        import wave
    except ImportError:
        return False, None, "请安装: pip install sounddevice"

    try:
        duration = max(1, min(seconds, 30))
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
        return True, buf.getvalue(), ""
    except Exception as e:
        return False, None, str(e)


# ---------------------------------------------------------------------------
# 语音合成 (TTS)
# ---------------------------------------------------------------------------

# 推荐中文发音人: zh-CN-XiaoxiaoNeural(女), zh-CN-YunxiNeural(男)
DEFAULT_TTS_VOICE = "zh-CN-XiaoxiaoNeural"


def tts_to_file(text: str, output_path: str, voice: str = DEFAULT_TTS_VOICE) -> Tuple[bool, str]:
    """将文字合成为音频并保存到文件。传入的 Markdown 会先转为纯文本再合成。"""
    text = strip_markdown_for_tts(text)
    if not text.strip():
        return False, "文本为空"
    try:
        import edge_tts
        import asyncio
    except ImportError:
        return False, "请安装: pip install edge-tts"

    async def _run():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    try:
        asyncio.run(_run())
        return True, output_path
    except Exception as e:
        return False, str(e)


def tts_to_bytes(text: str, voice: str = DEFAULT_TTS_VOICE) -> Tuple[bool, Optional[bytes], str]:
    """将文字合成为音频，返回 MP3 字节。传入的 Markdown 会先转为纯文本再合成。"""
    text = strip_markdown_for_tts(text)
    if not text.strip():
        return False, None, "文本为空"
    try:
        import edge_tts
        import asyncio
        import io
    except ImportError:
        return False, None, "请安装: pip install edge-tts"

    async def _run():
        buf = io.BytesIO()
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        return buf.getvalue()

    try:
        data = asyncio.run(_run())
        return True, data, ""
    except Exception as e:
        return False, None, str(e)


def tts_play(text: str, voice: str = DEFAULT_TTS_VOICE) -> Tuple[bool, str]:
    """将文字合成并播放（写入临时文件后系统播放）。传入的 Markdown 会先转为纯文本。"""
    text = strip_markdown_for_tts(text)
    if not text.strip():
        return False, "文本为空"
    try:
        import tempfile
        import os
        import sys
        ok, path, err = tts_to_file(text, tempfile.mktemp(suffix=".mp3"), voice)
        if not ok:
            return False, err
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}" 2>/dev/null || true')
        return True, ""
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# 便捷入口：语音输入 -> 文本
# ---------------------------------------------------------------------------

def voice_to_text(record_seconds: int = 5, language: str = "zh-CN") -> Tuple[bool, str]:
    """
    录制麦克风并识别为文字。
    返回 (成功, 文本或错误信息)。
    """
    ok, wav_bytes, err = record_audio(record_seconds)
    if not ok:
        return False, err or "录音失败"
    return stt_from_bytes(wav_bytes, language)
