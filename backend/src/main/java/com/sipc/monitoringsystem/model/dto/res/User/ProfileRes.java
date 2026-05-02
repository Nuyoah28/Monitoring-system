package com.sipc.monitoringsystem.model.dto.res.User;

import com.sipc.monitoringsystem.model.po.User.User;
import lombok.Data;

@Data
public class ProfileRes {
    private Integer id;

    private String name;

    private String phone;

    private String avatarUrl;

    private Integer role;

    private Boolean isResident;

    private String homeArea;

    private Boolean notifyEnabled;

    public ProfileRes(User user) {
        this.id = user.getId();
        this.name = user.getUserName();
        this.phone = user.getPhone();
        this.avatarUrl = user.getAvatarUrl();
        this.role = user.getRole();
        this.isResident = user.getIsResident();
        this.homeArea = user.getHomeArea();
        this.notifyEnabled = user.getNotifyEnabled();
    }
}
