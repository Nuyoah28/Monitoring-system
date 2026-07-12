package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.config.OssConfig;
import com.sipc.monitoringsystem.dao.CommunityReportDao;
import com.sipc.monitoringsystem.model.po.CommunityReport.CommunityReportInfo;
import com.sipc.monitoringsystem.model.po.User.User;
import com.sipc.monitoringsystem.service.CommunityReportService;
import com.sipc.monitoringsystem.service.UserService;
import com.sipc.monitoringsystem.websocket.AlarmWebSocketServer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
public class CommunityReportServiceImpl extends ServiceImpl<CommunityReportDao, CommunityReportInfo>
        implements CommunityReportService {

    @Autowired
    private OssConfig ossConfig;

    @Autowired
    private UserService userService;

    @Override
    public List<CommunityReportInfo> listForUser(User currentUser) {
        QueryWrapper<CommunityReportInfo> wrapper = new QueryWrapper<>();
        // 业主(role=1)只看自己上报的；管理员(role=0)看全部
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
            wrapper.eq("owner_user_id", currentUser.getId());
        }
        wrapper.orderByDesc("report_time").orderByDesc("id");
        List<CommunityReportInfo> list = this.list(wrapper);
        list.forEach(this::fillImageUrls);
        return list;
    }

    @Override
    public CommunityReportInfo getById(Integer id, User currentUser) {
        CommunityReportInfo info = this.baseMapper.selectById(id);
        if (info == null) {
            return null;
        }
        if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())
                && !currentUser.getId().equals(info.getOwnerUserId())) {
            return null;
        }
        fillImageUrls(info);
        return info;
    }

    @Override
    public Integer create(CommunityReportInfo info, User currentUser) {
        try {
            if (info != null && currentUser != null) {
                info.setOwnerUserId(currentUser.getId());
                if (info.getPublisher() == null || info.getPublisher().trim().isEmpty()) {
                    info.setPublisher(currentUser.getUserName());
                }
            }
            if (info != null && info.getStatus() == null) {
                info.setStatus(0);
            }
            if (info != null && info.getReportTime() == null) {
                info.setReportTime(new Timestamp(System.currentTimeMillis()));
            }
            this.save(info);
            pushToManagers(info);
            return info.getId();
        } catch (Exception e) {
            log.error("创建社区上报失败", e);
            return -1;
        }
    }

    @Override
    public boolean handle(Integer id, Integer status, String reply, User currentUser) {
        try {
            CommunityReportInfo existing = this.baseMapper.selectById(id);
            if (existing == null) {
                return false;
            }
            if (status != null) {
                existing.setStatus(status);
            }
            existing.setHandleReply(reply);
            existing.setHandleTime(new Timestamp(System.currentTimeMillis()));
            if (currentUser != null) {
                existing.setHandler(currentUser.getUserName());
            }
            return this.updateById(existing);
        } catch (Exception e) {
            log.error("处理社区上报失败", e);
            return false;
        }
    }

    @Override
    public boolean delete(Integer id, User currentUser) {
        try {
            // 业主只能删自己的，管理员可删任意
            if (currentUser != null && Integer.valueOf(1).equals(currentUser.getRole())) {
                CommunityReportInfo existing = this.baseMapper.selectById(id);
                if (existing == null || !currentUser.getId().equals(existing.getOwnerUserId())) {
                    return false;
                }
            }
            return this.removeById(id);
        } catch (Exception e) {
            log.error("删除社区上报失败", e);
            return false;
        }
    }

    /** 把逗号分隔的 image_keys 拼成完整 COS 访问 URL 列表，写入派生字段供前端展示 */
    private void fillImageUrls(CommunityReportInfo info) {
        if (info == null) {
            return;
        }
        List<String> urls = new ArrayList<>();
        String keys = info.getImageKeys();
        if (keys != null && !keys.trim().isEmpty()) {
            for (String key : keys.split(",")) {
                String trimmed = key.trim();
                if (trimmed.isEmpty()) {
                    continue;
                }
                try {
                    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
                        urls.add(trimmed);
                    } else {
                        urls.add(ossConfig.buildObjectUrl(trimmed));
                    }
                } catch (Exception e) {
                    log.warn("拼接上报图片URL失败: {}", trimmed, e);
                }
            }
        }
        info.setImageUrls(urls);
    }

    /** 业主上报后，复用报警 WebSocket 通道实时推送给所有管理端账号 */
    private void pushToManagers(CommunityReportInfo info) {
        try {
            List<User> managers = userService.list(new QueryWrapper<User>().eq("role", 0));
            if (managers == null || managers.isEmpty()) {
                return;
            }
            List<String> managerIds = managers.stream()
                    .map(user -> String.valueOf(user.getId()))
                    .collect(Collectors.toList());
            fillImageUrls(info);
            Map<String, Object> message = new HashMap<>();
            message.put("type", "NEW_REPORT");
            message.put("message", "有居民上报新的社区问题，请及时查看处理");
            message.put("data", info);
            AlarmWebSocketServer.sendToUsers(managerIds, message);
        } catch (Exception e) {
            log.warn("推送社区上报通知失败", e);
        }
    }
}
