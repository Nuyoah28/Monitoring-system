package com.sipc.monitoringsystem.model.dto.param.user;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class LoginParam {
    @NotNull(message = "username不能为空")
    public String userName;

    @NotNull(message = "password不能为空")
    public String password;
}
