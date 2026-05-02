package com.sipc.monitoringsystem.model.dto.res.parking;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ParkingTrafficFlowTrendPointRes {
    private String label;
    private Integer inCount;
    private Integer outCount;
    private Integer totalFlow;
}
