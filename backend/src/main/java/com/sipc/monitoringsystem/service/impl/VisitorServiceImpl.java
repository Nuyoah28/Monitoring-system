package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.VisitorDao;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import com.sipc.monitoringsystem.service.VisitorService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class VisitorServiceImpl extends ServiceImpl<VisitorDao, VisitorInfo> implements VisitorService {

    @Override
    public List<VisitorInfo> listAll(User currentUser) {
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
            return this.list(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<VisitorInfo>()
                    .eq("owner_user_id", currentUser.getId())
                    .orderByDesc("visit_time")
                    .orderByDesc("id"));
        }
        return this.list(new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<VisitorInfo>()
                .orderByDesc("visit_time")
                .orderByDesc("id"));
    }

    @Override
    public VisitorInfo getById(Integer id, User currentUser) {
        VisitorInfo info = this.baseMapper.selectById(id);
        if (info == null) {
            return null;
        }
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
            return currentUser.getId().equals(info.getOwnerUserId()) ? info : null;
        }
        return info;
    }

    @Override
    public Integer create(VisitorInfo info, User currentUser) {
        try {
            if (info != null && currentUser != null) {
                info.setOwnerUserId(currentUser.getId());
            }
            this.save(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建访客信息失败", e);
            return -1;
        }
    }

    @Override
    public boolean update(VisitorInfo info, User currentUser) {
        try {
            if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
                VisitorInfo existing = this.baseMapper.selectById(info.getId());
                if (existing == null || !currentUser.getId().equals(existing.getOwnerUserId())) {
                    return false;
                }
                info.setOwnerUserId(existing.getOwnerUserId());
            }
            return this.updateById(info);
        } catch (Exception e) {
            log.error("更新访客信息失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id, User currentUser) {
        try {
            if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
                VisitorInfo existing = this.baseMapper.selectById(id);
                if (existing == null || !currentUser.getId().equals(existing.getOwnerUserId())) {
                    return false;
                }
            }
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除访客信息失败", e);
            return false;
        }
    }
}
