package com.sipc.monitoringsystem.model.dto.res.User;

import lombok.Data;

/**
 * @author CZCZCZ
 * &#064;date 2023-09-10 17:29
 */

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
