from __future__ import annotations

import hashlib
import time
from typing import Any, Callable

import requests
from flask import Blueprint, current_app, jsonify, request

from agent_core.config.settings import AgentSettings


def create_qq_gateway_blueprint(get_agent: Callable[[], Any], agent_executor, settings: AgentSettings) -> Blueprint:
    bp = Blueprint("qq_gateway", __name__)

    @bp.route("/gateway/qq/ping", methods=["GET"])
    def ping():
        return jsonify({"code": "00000", "message": "ok", "data": {"enabled": settings.qq_gateway_enabled}})

    @bp.route("/gateway/qq/webhook", methods=["POST"])
    def qq_webhook():
        if not settings.qq_gateway_enabled:
            return jsonify({"code": "A1000", "message": "QQ gateway disabled", "data": None}), 403

        payload = request.get_json(silent=True) or {}
        token = (request.headers.get("X-QQ-Token") or "").strip()
        expected = (settings.qq_gateway_verify_token or "").strip()
        if expected and token != expected:
            return jsonify({"code": "A1000", "message": "invalid token", "data": None}), 401

        message_type = str(payload.get("message_type") or "")
        raw_message = str(payload.get("raw_message") or "").strip()
        user_id = str(payload.get("user_id") or "")
        group_id = str(payload.get("group_id") or "")
        self_id = str(payload.get("self_id") or "")

        if not raw_message:
            return jsonify({"code": "00000", "message": "ignored empty message", "data": None})

        if message_type == "group" and settings.qq_group_require_at and self_id:
            at_token = f"[CQ:at,qq={self_id}]"
            if at_token not in raw_message and f"@{self_id}" not in raw_message:
                return jsonify({"code": "00000", "message": "ignored without at", "data": None})

        question = _sanitize_question(raw_message, self_id=self_id)
        if not question:
            return jsonify({"code": "00000", "message": "ignored empty question", "data": None})

        conversation_key = _build_qq_conversation_key(message_type, group_id, user_id)
        start = time.time()
        try:
            agent = get_agent()
            if agent is None:
                return jsonify({"code": "A1000", "message": "agent not ready", "data": None}), 503
            answer = agent_executor.submit(
                agent.process_question,
                question,
                user_token=user_id or None,
                conversation_key=conversation_key,
            ).result()
            elapsed_ms = int((time.time() - start) * 1000)
            _reply_to_qq(payload, answer, settings)
            current_app.logger.info("QQ gateway handled in %sms", elapsed_ms)
            return jsonify({"code": "00000", "message": "ok", "data": {"elapsed_ms": elapsed_ms}})
        except Exception as exc:
            current_app.logger.exception("QQ gateway handle failed: %s", exc)
            _reply_to_qq(payload, "抱歉，智能助手暂时不可用，请稍后重试。", settings)
            return jsonify({"code": "A1000", "message": "gateway failed", "data": None}), 500

    return bp


def _sanitize_question(raw_message: str, *, self_id: str) -> str:
    text = raw_message
    if self_id:
        text = text.replace(f"[CQ:at,qq={self_id}]", " ")
        text = text.replace(f"@{self_id}", " ")
    return " ".join(text.split()).strip()


def _build_qq_conversation_key(message_type: str, group_id: str, user_id: str) -> str:
    source = f"qq|{message_type}|{group_id}|{user_id}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:16]
    scope = f"group:{group_id}" if message_type == "group" and group_id else f"user:{user_id or 'unknown'}"
    return f"qq:{scope}:{digest}"


def _reply_to_qq(payload: dict[str, Any], answer: str, settings: AgentSettings) -> None:
    message_type = str(payload.get("message_type") or "")
    user_id = payload.get("user_id")
    group_id = payload.get("group_id")
    if message_type == "group" and group_id:
        endpoint = "/send_group_msg"
        body = {"group_id": group_id, "message": answer}
    else:
        endpoint = "/send_private_msg"
        body = {"user_id": user_id, "message": answer}

    url = f"{settings.qq_api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if settings.qq_api_access_token:
        headers["Authorization"] = f"Bearer {settings.qq_api_access_token}"
    requests.post(url, json=body, headers=headers, timeout=settings.qq_request_timeout_seconds)
