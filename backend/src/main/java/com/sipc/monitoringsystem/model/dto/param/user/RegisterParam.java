package com.sipc.monitoringsystem.model.dto.param.user;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class RegisterParam {
    @NotNull(message = "username不能为空")
    private String username;

    @NotNull(message = "password不能为空")
    private String password;

    @NotNull(message = "role不能为空")
    private Integer role;

    private String homeArea;
}
