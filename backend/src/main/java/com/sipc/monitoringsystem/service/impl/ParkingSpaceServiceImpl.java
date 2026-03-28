package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.ParkingSpaceDao;
import com.sipc.monitoringsystem.model.po.Parking.ParkingSpaceInfo;
import com.sipc.monitoringsystem.service.ParkingSpaceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class ParkingSpaceServiceImpl extends ServiceImpl<ParkingSpaceDao, ParkingSpaceInfo> implements ParkingSpaceService {

    @Override
    public List<ParkingSpaceInfo> listAll() {
        return this.list();
    }

    @Override
    public ParkingSpaceInfo getById(Integer id) {
        return this.baseMapper.selectById(id);
    }

    @Override
    public Integer create(ParkingSpaceInfo info) {
        try {
            this.save(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建车位信息失败", e);
            return -1;
        }
    }

    @Override
    public boolean update(ParkingSpaceInfo info) {
        try {
            return this.updateById(info);
        } catch (Exception e) {
            log.error("更新车位信息失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id) {
        try {
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除车位信息失败", e);
            return false;
        }
    }
}
