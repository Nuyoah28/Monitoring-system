package com.sipc.monitoringsystem.model.dto.param.iot;

import lombok.Data;

import java.util.List;

@Data
public class ReportParkingParam {
    private Integer monitorId;
    private String deviceCode;
    private List<ZoneReport> zones;

    @Data
    public static class ZoneReport {
        private String areaCode;
        private String areaName;
        private Integer totalSpaces;
        private Integer occupiedSpaces;
    }
}
