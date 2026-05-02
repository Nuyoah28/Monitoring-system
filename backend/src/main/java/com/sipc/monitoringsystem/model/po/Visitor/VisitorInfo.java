package com.sipc.monitoringsystem.model.po.Visitor;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
@TableName("visitor_info")
public class VisitorInfo {
    @TableId(type = IdType.AUTO)
    private Integer id;

    @TableField("visitor_name")
    private String visitorName;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField("visit_time")
    private Timestamp visitTime;

    @TableField("plate_number")
    private String plateNumber;

    @TableField("owner_user_id")
    private Integer ownerUserId;

    public Integer getId() {
        return id;
    }
}
