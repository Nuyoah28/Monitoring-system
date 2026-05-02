package com.sipc.monitoringsystem.model.dto.res.Monitor;

import com.sipc.monitoringsystem.model.po.Monitor.MonitorRecognitionRule;
import lombok.Data;

@Data
public class MonitorRecognitionRuleRes {
    private Long id;
    private Integer monitorId;
    private String name;
    private String prompt;
    private String translatedPrompt;
    private Integer riskLevel;
    private String alertHint;
    private Boolean enabled;

    public MonitorRecognitionRuleRes(MonitorRecognitionRule rule) {
        this.id = rule.getId();
        this.monitorId = rule.getMonitorId();
        this.name = rule.getName();
        this.prompt = rule.getPrompt();
        this.translatedPrompt = rule.getTranslatedPrompt();
        this.riskLevel = rule.getRiskLevel();
        this.alertHint = rule.getAlertHint();
        this.enabled = rule.getEnabled();
    }
}
