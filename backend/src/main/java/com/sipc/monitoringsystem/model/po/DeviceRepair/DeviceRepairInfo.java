package com.sipc.monitoringsystem.model.po.DeviceRepair;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
@TableName("device_repair_info")
public class DeviceRepairInfo {
    @TableId(type = IdType.AUTO)
    private Integer id;

    @TableField("device_name")
    private String deviceName;

    private String location;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField("report_time")
    private Timestamp reportTime;

    @TableField("repair_detail")
    private String repairDetail;

    private String publisher;

    @TableField("owner_user_id")
    private Integer ownerUserId;

    public Integer getId() {
        return id;
    }
}
