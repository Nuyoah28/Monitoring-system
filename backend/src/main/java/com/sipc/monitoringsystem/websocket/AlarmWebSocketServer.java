package com.sipc.monitoringsystem.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.websocket.*;
import jakarta.websocket.server.PathParam;
import jakarta.websocket.server.ServerEndpoint;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket 报警推送服务端
 * 连接地址: ws://localhost:10215/ws/alarm/{userId}
 * 
 * @author Fengboxuan
 *         &#064;date 2026-02-05 16:09
 */
@Slf4j
@Component
@ServerEndpoint("/ws/alarm/{userId}")
public class AlarmWebSocketServer {

    private static final Map<String, java.util.concurrent.CopyOnWriteArraySet<Session>> onlineSessions = new ConcurrentHashMap<>();
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @OnOpen
    public void onOpen(Session session, @PathParam("userId") String userId) {
        onlineSessions.computeIfAbsent(userId, k -> new java.util.concurrent.CopyOnWriteArraySet<>()).add(session);
        log.info("WebSocket 连接建立: userId={}, sessionId={}, 当前用户数: {}",
                userId, session.getId(), onlineSessions.size());
    }

    @OnClose
    public void onClose(Session session, @PathParam("userId") String userId) {
        java.util.concurrent.CopyOnWriteArraySet<Session> userSessions = onlineSessions.get(userId);
        if (userSessions != null) {
            userSessions.remove(session);
            if (userSessions.isEmpty()) {
                onlineSessions.remove(userId);
            }
        }
        log.info("WebSocket 连接关闭: userId={}, sessionId={}", userId, session.getId());
    }

    @OnMessage
    public void onMessage(String message, Session session, @PathParam("userId") String userId) {
        log.debug("收到客户端消息: userId={}, message={}", userId, message);
        if ("ping".equals(message)) {
            try {
                session.getBasicRemote().sendText("pong");
            } catch (IOException e) {
                log.error("发送心跳响应失败: userId={}", userId, e);
            }
        }
    }

    @OnError
    public void onError(Session session, Throwable error, @PathParam("userId") String userId) {
        log.error("WebSocket 错误: userId={}, sessionId={}", userId, session.getId(), error);
        // Remove session on error
        java.util.concurrent.CopyOnWriteArraySet<Session> userSessions = onlineSessions.get(userId);
        if (userSessions != null) {
            userSessions.remove(session);
            if (userSessions.isEmpty()) {
                onlineSessions.remove(userId);
            }
        }
    }

    public static void sendToAll(Object message) {
        String jsonStr;
        try {
            jsonStr = objectMapper.writeValueAsString(message);
        } catch (IOException e) {
            log.error("消息序列化失败", e);
            return;
        }

        log.info("开始广播消息");
        if (onlineSessions.isEmpty()) {
            return;
        }

        for (Map.Entry<String, java.util.concurrent.CopyOnWriteArraySet<Session>> entry : onlineSessions.entrySet()) {
            String userId = entry.getKey();
            for (Session session : entry.getValue()) {
                if (session.isOpen()) {
                    try {
                        session.getBasicRemote().sendText(jsonStr);
                    } catch (IOException e) {
                        log.error("广播消息失败: userId={}, sessionId={}", userId, session.getId(), e);
                    }
                }
            }
        }
        log.info("广播结束");
    }

    public static void sendToUsers(java.util.List<String> userIds, Object message) {
        String jsonStr;
        try {
            jsonStr = objectMapper.writeValueAsString(message);
        } catch (IOException e) {
            log.error("消息序列化失败", e);
            return;
        }

        if (onlineSessions.isEmpty() || userIds == null || userIds.isEmpty()) {
            return;
        }

        for (String userId : userIds) {
            java.util.concurrent.CopyOnWriteArraySet<Session> userSessions = onlineSessions.get(userId);
            if (userSessions != null) {
                for (Session session : userSessions) {
                    if (session.isOpen()) {
                        try {
                            session.getBasicRemote().sendText(jsonStr);
                        } catch (IOException e) {
                            log.error("定向发送消息失败: userId={}, sessionId={}", userId, session.getId(), e);
                        }
                    }
                }
            }
        }
    }

    public static int getOnlineCount() {
        return onlineSessions.size();
    }
}
