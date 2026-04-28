package com.sipc.monitoringsystem.model.po.Parking;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
@TableName("parking_area_status")
public class ParkingAreaStatus {
    @TableId(type = IdType.AUTO)
    private Integer id;

    private Integer monitorId;

    private String deviceCode;

    private String areaCode;

    private String areaName;

    private Integer totalSpaces;

    private Integer occupiedSpaces;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT)
    private Timestamp createTime;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Timestamp updateTime;
}
