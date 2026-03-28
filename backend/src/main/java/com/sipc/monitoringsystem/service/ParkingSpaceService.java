package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.Parking.ParkingSpaceInfo;

import java.util.List;

public interface ParkingSpaceService {
    List<ParkingSpaceInfo> listAll();

    ParkingSpaceInfo getById(Integer id);

    Integer create(ParkingSpaceInfo info);

    boolean update(ParkingSpaceInfo info);

    boolean delete(Integer id);
}
