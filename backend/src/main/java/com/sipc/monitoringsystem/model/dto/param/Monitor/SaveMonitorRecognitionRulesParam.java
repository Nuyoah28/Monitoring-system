package com.sipc.monitoringsystem.model.dto.param.Monitor;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class SaveMonitorRecognitionRulesParam {
    private List<RuleItem> rules = new ArrayList<>();

    @Data
    public static class RuleItem {
        private Long id;
        private String name;
        private String prompt;
        private String translatedPrompt;
        private Integer riskLevel;
        private String alertHint;
        private Boolean enabled;
    }
}
