package com.sipc.monitoringsystem.service;

import java.util.List;


public interface RequestFlaskService
{
    Boolean updateMonitorArea(String ip, List<Integer> area) throws Exception;

    Boolean updateMonitorAbility(String ip,List<Boolean> ability) throws Exception;

    String getMonitorImg(String ip) throws Exception;
}
