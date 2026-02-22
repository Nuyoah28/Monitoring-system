package com.sipc.monitoringsystem.model.po.User;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableField;
import lombok.Data;

import java.io.Serializable;

/**
 * @author CZCZCZ
 *         &#064;date 2023-09-10 17:11
 */
@Data
@TableName("user_info")
public class User implements Serializable {
    @TableId(type = IdType.AUTO)
    private Integer id;

    @TableField("user_name")
    private String userName;

    private String password;

    private String phone;

    private Integer role;
}
