package com.sipc.monitoringsystem.aop;

import org.springframework.cache.annotation.CacheEvict;
import org.springframework.stereotype.Service;


@Service
public class ClearRedisImpl
{
    @CacheEvict(value = "cache",allEntries = true)
    public void deleteCache(){ // 空方法，目的只有触发CacheEvict注解
    }
}
