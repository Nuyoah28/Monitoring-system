package com.sipc.monitoringsystem.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.model.dto.res.FlaskResponse.updateMonitorAreaRes;
import com.sipc.monitoringsystem.service.RequestFlaskService;
import com.sipc.monitoringsystem.util.HttpUtils;
import com.sipc.monitoringsystem.util.JacksonUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author CZCZCZ
 * &#064;date 2023-10-03 15:08
 */
@Service
@Slf4j
public class RequestFlaskServiceImpl implements RequestFlaskService {

    private final String FLASK_TOKEN = "sipc115";



    @Override
    public Boolean updateMonitorArea(String ip, List<Integer> area) throws Exception{
        if (area == null || area.isEmpty()) {
            return false;
        }
        boolean validArea = area.size() >= 4
                && area.get(0) != null
                && area.get(1) != null
                && area.get(2) != null
                && area.get(3) != null;
        if (!validArea) {
            return false;
        }
        Map<String,Object> mp = new HashMap<>();
        mp.put("areaList",area);
        ObjectMapper objectMapper = new ObjectMapper();
        String json = objectMapper.writeValueAsString(mp);
        String response = HttpUtils.postJson("https://"+ip+"/api/v1/monitor-device/area",json,FLASK_TOKEN);
        updateMonitorAreaRes res = JacksonUtils.json2pojo(response, updateMonitorAreaRes.class);
        return res != null && "success".equals(res.getMsg());
    }

    @Override
    public Boolean updateMonitorAbility(String ip,List<Boolean> ability) throws Exception{
        if (ability == null || ability.isEmpty()) {
            return false;
        }
        Map<String,Object> mp = new HashMap<>();
        mp.put("typeList",ability);
        ObjectMapper objectMapper = new ObjectMapper();
        String json = objectMapper.writeValueAsString(mp);
        String response = HttpUtils.postJson("https://"+ip+"/api/v1/monitor-device/type",json,FLASK_TOKEN);
        updateMonitorAreaRes res = JacksonUtils.json2pojo(response, updateMonitorAreaRes.class);
        return res != null && "success".equals(res.getMsg());
    }

    @Override
    @Cacheable(value = "MonitorImg",key = "#ip",unless = "#result==null")
    public String getMonitorImg(String ip) throws RuntimeException{
        return HttpUtils.GetBase64("https://"+ip+"/api/v1/monitor-device/image",FLASK_TOKEN);
    }
}
