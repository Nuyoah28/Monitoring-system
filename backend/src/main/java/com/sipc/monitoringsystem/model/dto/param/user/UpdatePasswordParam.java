package com.sipc.monitoringsystem.model.dto.param.user;

import lombok.Data;


@Data
public class UpdatePasswordParam {
    private String oldPassword;
    private String newPassword;
}
