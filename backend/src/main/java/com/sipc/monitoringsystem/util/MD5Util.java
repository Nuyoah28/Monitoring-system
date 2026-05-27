package com.sipc.monitoringsystem.util;

import org.springframework.util.DigestUtils;

import java.nio.charset.StandardCharsets;

public class MD5Util {

    public static final String salt = "HuaWuWin!";

    public static String MD5Encode(String password) {
        String md5 = null;
        md5 = DigestUtils.md5DigestAsHex((password + salt).getBytes(StandardCharsets.UTF_8));
        return md5;
    }


}
