package com.sipc.monitoringsystem.sparkdesk;

import cn.hutool.core.util.StrUtil;
import com.alibaba.druid.util.StringUtils;
import com.sipc.monitoringsystem.util.JwtUtils;
import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnMessage;
import jakarta.websocket.OnOpen;
import jakarta.websocket.server.PathParam;
import jakarta.websocket.server.ServerEndpoint;
import lombok.extern.slf4j.Slf4j;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.WebSocket;
import org.springframework.stereotype.Component;

import jakarta.websocket.Session;
import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;

//@ServerEndpoint(value = "/websocketClient/{userId}")
@ServerEndpoint(value = "/api/v1/gpt/ws/{token}")
@Component
@Slf4j
public class WebSocketClient {


    /**
     * 静态变量，用来记录当前在线连接数。应该把它设计成线程安全的
     */

    private static int onlineCount = 0;

    /**
     * concurrent包的线程安全Map，用来存放每个客户端对应的MyWebSocket对象
     */
    private static final ConcurrentHashMap<String, WebSocketClient> webSocketMap = new ConcurrentHashMap<>();

    public ConcurrentHashMap<String, WebSocketClient> getWebSocketMap() {
        return webSocketMap;
    }

    /**
     * 与某个客户端的连接会话，需要通过它来给客户端发送数据
     */
    private Session session;

    /**
     * 用户id 唯一标识
     */
    private String token;

    /**
     * 连接建立成功调用的方法
     */
    @OnOpen
    public void onOpen(Session session, @PathParam("token") String token) {
        if ((!org.springframework.util.StringUtils.hasLength(token)) || (!JwtUtils.verify(token))) {
            log.error("WebSocket token错误!");
            throw new RuntimeException("鉴权异常");
        }
        this.session = session;
        //加入map
        webSocketMap.put(session.getId(), this);
        log.info("WebSocket opened: " + session.getId());
        this.session = session;
        this.token = token;
        //在线数加1
        addOnlineCount();
        log.info("WebSocket客户端{}连接成功，当前在线人数：{}", session.getId(), getOnlineCount());
    }

    /**
     * 连接关闭调用的方法
     */
    @OnClose
    public void onClose() {
        //从map中删除
        webSocketMap.remove(session.getId());
        //在线数减1
        subOnlineCount();
        log.info("WebSocket客户端{}连接断开，当前在线人数：{}", session.getId(), getOnlineCount());
    }

    /**
     * 收到客户端消息后调用的方法
     *
     * @param message 客户端发送过来的消息
     */
    @OnMessage
    public void onMessage(String message, Session session) throws Exception {
        // 心跳检测响应
        if (StringUtils.equalsIgnoreCase("ping", message)) {
            sendMessage("pong");
            log.info("WebSocket服务端已回复客户端{}的心跳检测:pong", session.getId());
            return;
        }
        BigModelNew.NewQuestion = message;
        // 构建鉴权url
        String authUrl = BigModelNew.getAuthUrl(BigModelNew.hostUrl, BigModelNew.apiKey, BigModelNew.apiSecret);
        OkHttpClient client = new OkHttpClient.Builder().build();
        String url = authUrl.toString().replace("http://", "ws://").replace("https://", "wss://");
        Request request = new Request.Builder().url(url).build();
        for (int i = 0; i < 1; i++) {
            BigModelNew.totalAnswer = "";
            WebSocket webSocket = client.newWebSocket(request, new BigModelNew(i + "",
                    false));
        }
        log.info("收到客户端{}的消息：{}", session.getId(), message);
    }

    /**
     * 发生错误时调用
     */
    @OnError
    public void onError(Session session, Throwable error) {
        log.error("发生错误{}", session.getId(), error);
        error.printStackTrace();
    }

    /**
     * 向客户端发送消息
     */
    public void sendMessage(String message) {
        try {
            this.session.getBasicRemote().sendText(message);
        } catch (IOException e) {
            e.printStackTrace();
            log.error("客户端{}发送消息{{}}失败", session.getId(), message);
        }
    }

//    /**
//     * 通过userId向客户端发送消息
//     */
//    public static void sendMessageByUserId(String userId, String message) throws IOException {
//        log.info("给用户{}发送{}信息", userId, message);
//        if (StrUtil.isNotBlank(userId) && webSocketMap.containsKey(userId)) {
//            webSocketMap.get(userId).sendMessage(message);
//        }
//    }

    /**
     * 关闭WebSocket
     *
     * @param userId 用户id
     */
    public static void closeWebSocket(String userId) {
        if (StrUtil.isNotBlank(userId) && webSocketMap.containsKey(userId)) {
            webSocketMap.get(userId).onClose();
        }
    }

    /**
     * 群发自定义消息
     */
    public static void sendInfo(String message) {
        for (String item : webSocketMap.keySet()) {
            webSocketMap.get(item).sendMessage(message);
        }
    }

    /**
     * 获取在线人数
     *
     * @return 在线人数
     */
    public static synchronized int getOnlineCount() {
        return onlineCount;
    }

    /**
     * 添加一位在线人数
     */
    public static synchronized void addOnlineCount() {
        WebSocketClient.onlineCount++;
    }

    /**
     * 减少一位在线人数
     */
    public static synchronized void subOnlineCount() {
        WebSocketClient.onlineCount--;
    }

}
