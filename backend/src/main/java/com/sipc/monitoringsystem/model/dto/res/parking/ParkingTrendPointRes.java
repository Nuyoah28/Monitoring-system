package com.sipc.monitoringsystem.model.dto.res.parking;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ParkingTrendPointRes {
    private String label;
    private Integer occupancy;
    private Integer used;
}
