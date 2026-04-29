package com.sipc.monitoringsystem.model.dto.res.parking;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;
import java.util.List;

@Data
public class ParkingRealtimeRes {
    private Integer monitorId;
    private String source;
    private Integer totalSpaces;
    private Integer occupiedSpaces;
    private Integer freeSpaces;
    private Integer occupancyRate;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp updateTime;

    private List<ZoneItem> zones;

    @Data
    public static class ZoneItem {
        private String areaCode;
        private String areaName;
        private Integer totalSpaces;
        private Integer occupiedSpaces;
    }
}
