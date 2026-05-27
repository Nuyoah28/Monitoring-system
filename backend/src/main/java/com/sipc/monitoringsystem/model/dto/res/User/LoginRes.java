package com.sipc.monitoringsystem.model.dto.res.User;

import lombok.Data;


@Data
public class LoginRes {

    private Integer id;

    private String name;



    private String phone;

    private Integer role;

    private String avatarUrl;

    private String homeArea;

    private Boolean notifyEnabled;

    private String token;

}
