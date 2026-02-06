package com.sipc.monitoringsystem.util;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.Date;

public class JwtUtils {
    //有效期为30天（延长到30天，减少过期问题）
    public static final long EXPIRE_TIME = (long) 1000 * 60 * 60 * 24 * 30;
    public static final String SECRET = "SIPC115";

    public static String signUser(User user) {
        Date expireDate = new Date(System.currentTimeMillis() + EXPIRE_TIME);
        return JWT.create()
                .withClaim("id",user.getId())
                .withClaim("role", user.getRole())
                .withExpiresAt(expireDate)
                .sign(Algorithm.HMAC256(SECRET));
    }

    public static String signMonitor(Integer id){
        return JWT.create()
                .withClaim("id",id)
                .sign(Algorithm.HMAC256(SECRET));
    }

    public static boolean verify(String token) {
        try {
            JWTVerifier verifier = JWT.require(Algorithm.HMAC256(SECRET)).build();
            DecodedJWT decodedJWT = verifier.verify(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 验证token并返回详细信息
     * @param token JWT token
     * @return "OK" 如果验证成功，否则返回错误信息
     */
    public static String verifyWithDetail(String token) {
        try {
            JWTVerifier verifier = JWT.require(Algorithm.HMAC256(SECRET)).build();
            DecodedJWT decodedJWT = verifier.verify(token);
            return "OK";
        } catch (com.auth0.jwt.exceptions.TokenExpiredException e) {
            return "Token已过期";
        } catch (com.auth0.jwt.exceptions.JWTDecodeException e) {
            return "Token格式错误";
        } catch (com.auth0.jwt.exceptions.SignatureVerificationException e) {
            return "Token签名验证失败";
        } catch (Exception e) {
            return "Token验证失败: " + e.getMessage();
        }
    }

    /**
     * 从token中获取用户信息（不验证过期，用于刷新token）
     */
    public static User getUserByToken(String token) {
        DecodedJWT decodedJWT = JWT.decode(token);
        User user = new User();
        user.setId(decodedJWT.getClaim("id").asInt());
        user.setRole(decodedJWT.getClaim("role").asInt());
        return user;
    }
    
    /**
     * 检查token是否即将过期（剩余时间少于7天）
     */
    public static boolean isTokenExpiringSoon(String token) {
        try {
            DecodedJWT decodedJWT = JWT.decode(token);
            Date expiresAt = decodedJWT.getExpiresAt();
            if (expiresAt == null) {
                return true; // 没有过期时间，认为即将过期
            }
            long remainingTime = expiresAt.getTime() - System.currentTimeMillis();
            long sevenDays = 7L * 24 * 60 * 60 * 1000; // 7天的毫秒数
            return remainingTime < sevenDays;
        } catch (Exception e) {
            return true; // 解析失败，认为即将过期
        }
    }

    public static Monitor getMonitorByToken(String token){
        DecodedJWT decodedJWT = JWT.decode(token);
        Monitor monitor = new Monitor();
        monitor.setId(decodedJWT.getClaim("id").asInt());
        return monitor;
    }

}