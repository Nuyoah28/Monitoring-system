package com.sipc.monitoringsystem.model.dto.res.Alarm;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 类型 × 区域热力矩阵统计结果
 */
@Data
public class GetTypeAreaHeatRes {
    private Integer defer;
    private String rangeLabel;
    private Long total;
    private List<RankItem> byType;
    private List<RankItem> byArea;
    private List<String> types;
    private List<HeatRow> rows;
    private Long maxCount;

    @Data
    public static class RankItem {
        private String name;
        private Long count;

        public RankItem(String name, Long count) {
            this.name = name;
            this.count = count;
        }
    }

    @Data
    public static class HeatRow {
        private String area;
        private Map<String, Long> values;

        public HeatRow(String area, Map<String, Long> values) {
            this.area = area;
            this.values = values;
        }
    }
}
