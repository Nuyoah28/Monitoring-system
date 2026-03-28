package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.VisitorDao;
import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import com.sipc.monitoringsystem.service.VisitorService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class VisitorServiceImpl extends ServiceImpl<VisitorDao, VisitorInfo> implements VisitorService {

    @Override
    public List<VisitorInfo> listAll() {
        return this.list();
    }

    @Override
    public VisitorInfo getById(Integer id) {
        return this.baseMapper.selectById(id);
    }

    @Override
    public Integer create(VisitorInfo info) {
        try {
            this.save(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建访客信息失败", e);
            return -1;
        }
    }

    @Override
    public boolean update(VisitorInfo info) {
        try {
            return this.updateById(info);
        } catch (Exception e) {
            log.error("更新访客信息失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id) {
        try {
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除访客信息失败", e);
            return false;
        }
    }
}
