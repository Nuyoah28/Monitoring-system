package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.dto.param.Monitor.SaveMonitorRecognitionRulesParam;
import com.sipc.monitoringsystem.model.dto.res.Monitor.MonitorRecognitionRuleRes;

import java.util.List;

public interface MonitorRecognitionRuleService {
    List<MonitorRecognitionRuleRes> getRulesByMonitorId(Integer monitorId);

    List<MonitorRecognitionRuleRes> saveRules(Integer monitorId, SaveMonitorRecognitionRulesParam param);
}
