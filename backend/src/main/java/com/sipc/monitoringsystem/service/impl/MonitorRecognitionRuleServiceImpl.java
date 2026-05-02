package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.MonitorRecognitionRuleDao;
import com.sipc.monitoringsystem.model.dto.param.Monitor.SaveMonitorRecognitionRulesParam;
import com.sipc.monitoringsystem.model.dto.res.Monitor.MonitorRecognitionRuleRes;
import com.sipc.monitoringsystem.model.po.Monitor.MonitorRecognitionRule;
import com.sipc.monitoringsystem.service.MonitorRecognitionRuleService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
public class MonitorRecognitionRuleServiceImpl extends ServiceImpl<MonitorRecognitionRuleDao, MonitorRecognitionRule>
        implements MonitorRecognitionRuleService {

    @Value("${algorithm.api.url:http://localhost:6006}")
    private String algorithmApiUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public List<MonitorRecognitionRuleRes> getRulesByMonitorId(Integer monitorId) {
        List<MonitorRecognitionRule> rules = list(new LambdaQueryWrapper<MonitorRecognitionRule>()
                .eq(MonitorRecognitionRule::getMonitorId, monitorId)
                .orderByAsc(MonitorRecognitionRule::getId));
        return rules.stream().map(MonitorRecognitionRuleRes::new).collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<MonitorRecognitionRuleRes> saveRules(Integer monitorId, SaveMonitorRecognitionRulesParam param) {
        remove(new QueryWrapper<MonitorRecognitionRule>().eq("monitor_id", monitorId));

        List<MonitorRecognitionRule> rules = buildRules(monitorId, param);
        if (!rules.isEmpty()) {
            saveBatch(rules);
        }

        List<String> translatedPrompts = syncEnabledPrompts(rules);
        if (!translatedPrompts.isEmpty()) {
            List<MonitorRecognitionRule> enabledRules = rules.stream()
                    .filter(rule -> Boolean.TRUE.equals(rule.getEnabled()))
                    .collect(Collectors.toList());
            for (int i = 0; i < enabledRules.size() && i < translatedPrompts.size(); i++) {
                enabledRules.get(i).setTranslatedPrompt(translatedPrompts.get(i));
            }
            updateBatchById(rules);
        }

        return getRulesByMonitorId(monitorId);
    }

    private List<MonitorRecognitionRule> buildRules(Integer monitorId, SaveMonitorRecognitionRulesParam param) {
        List<MonitorRecognitionRule> rules = new ArrayList<>();
        if (param == null || param.getRules() == null) {
            return rules;
        }
        for (SaveMonitorRecognitionRulesParam.RuleItem item : param.getRules()) {
            if (item == null || isBlank(item.getName()) || isBlank(item.getPrompt())) {
                continue;
            }
            MonitorRecognitionRule rule = new MonitorRecognitionRule();
            rule.setMonitorId(monitorId);
            rule.setName(item.getName().trim());
            rule.setPrompt(item.getPrompt().trim());
            rule.setTranslatedPrompt(trimToNull(item.getTranslatedPrompt()));
            rule.setRiskLevel(item.getRiskLevel() == null ? 2 : item.getRiskLevel());
            rule.setAlertHint(isBlank(item.getAlertHint()) ? "请及时查看现场情况" : item.getAlertHint().trim());
            rule.setEnabled(item.getEnabled() == null || item.getEnabled());
            rules.add(rule);
        }
        return rules;
    }

    private List<String> syncEnabledPrompts(List<MonitorRecognitionRule> rules) {
        List<String> prompts = rules.stream()
                .filter(rule -> Boolean.TRUE.equals(rule.getEnabled()))
                .map(MonitorRecognitionRule::getPrompt)
                .filter(prompt -> !isBlank(prompt))
                .collect(Collectors.toList());
        if (prompts.isEmpty()) {
            return new ArrayList<>();
        }
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("prompts", prompts);
            String targetUrl = algorithmApiUrl + "/api/v1/monitor-device/update_prompt";
            ResponseEntity<Map> response = restTemplate.postForEntity(targetUrl, body, Map.class);
            Map respBody = response.getBody();
            if (respBody == null || !"00000".equals(respBody.get("code"))) {
                log.warn("视觉算力节点返回规则同步失败: {}", respBody);
                return new ArrayList<>();
            }
            Object translated = respBody.get("translated");
            if (translated instanceof List<?>) {
                return ((List<?>) translated).stream()
                        .map(item -> item == null ? null : String.valueOf(item))
                        .collect(Collectors.toList());
            }
        } catch (Exception e) {
            log.warn("同步自定义识别规则到视觉算力节点失败", e);
        }
        return new ArrayList<>();
    }

    private boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private String trimToNull(String value) {
        return isBlank(value) ? null : value.trim();
    }
}
