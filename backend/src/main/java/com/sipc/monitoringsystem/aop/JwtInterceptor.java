package com.sipc.monitoringsystem.aop;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.model.dto.CommonResult;
import com.sipc.monitoringsystem.util.JwtUtils;
import com.sipc.monitoringsystem.util.RedisUtil;
import com.sipc.monitoringsystem.util.TokenThreadLocalUtil;
import jakarta.annotation.Resource;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;
@Slf4j
public class JwtInterceptor implements HandlerInterceptor {

    @Resource
    RedisUtil redisUtil;

    @Autowired
    ClearRedisImpl clearRedisImpl;

    @Override
    public boolean preHandle(HttpServletRequest request, @NotNull HttpServletResponse response, @NotNull Object handler) throws Exception {
        String authHeader = request.getHeader("Authorization");
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }
        //如果没有@Pass注解，直接放行
        Pass pass = handlerMethod.getMethodAnnotation(Pass.class);
        if (pass != null) {
            return true;
        }
        ClearRedis clearRedis = handlerMethod.getMethodAnnotation(ClearRedis.class);
        if (clearRedis != null) {
            //和redis配置类保持一致
            clearRedisImpl.deleteCache();
        }

        // 提取 token（处理 "Bearer " 前缀）
        String token = null;
        if (authHeader != null && !authHeader.isEmpty()) {
            if (authHeader.startsWith("Bearer ")) {
                token = authHeader.substring(7).trim();
            } else {
                token = authHeader.trim();
            }
        }

        // 验证 token
        if (token == null || token.isEmpty()) {
            response.setCharacterEncoding("UTF-8");
            response.setContentType("application/json; charset=utf-8");
            ObjectMapper objectMapper = new ObjectMapper();
            response.getWriter().println(objectMapper.writeValueAsString(CommonResult.tokenNull()));
            log.warn("token为空 - url: {}", request.getRequestURL());
            return false;
        }

        // 验证 token 有效性
        String verifyResult = JwtUtils.verifyWithDetail(token);
        if (!"OK".equals(verifyResult)) {
            response.setCharacterEncoding("UTF-8");
            response.setContentType("application/json; charset=utf-8");
            ObjectMapper objectMapper = new ObjectMapper();
            response.getWriter().println(objectMapper.writeValueAsString(CommonResult.tokenWrong()));
            log.warn("token验证失败 - 原因: {}, url: {}, token长度: {}", verifyResult, request.getRequestURL(), token.length());
            // 不记录完整 token（安全考虑），只记录前10个字符
            log.warn("token前缀: {}...", token.length() > 10 ? token.substring(0, 10) : token);
            return false;
        }

        // Token 验证通过，绑定到 ThreadLocal
        TokenThreadLocalUtil.getInstance().bind(token);
        return true;
    }

    @Override
    public void postHandle(@NotNull HttpServletRequest request, @NotNull HttpServletResponse response, @NotNull Object handler, ModelAndView modelAndView) throws Exception {
    }
//
    @Override
    public void afterCompletion(@NotNull HttpServletRequest request, @NotNull HttpServletResponse response, @NotNull Object handler, Exception ex) throws Exception {
    }

}
