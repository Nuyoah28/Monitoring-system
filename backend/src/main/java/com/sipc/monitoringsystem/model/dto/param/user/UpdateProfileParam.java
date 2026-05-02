package com.sipc.monitoringsystem.model.dto.param.user;

import lombok.Data;

@Data
public class UpdateProfileParam {
    private String userName;

    private String homeArea;

    private String avatarUrl;

    private Boolean notifyEnabled;
}
