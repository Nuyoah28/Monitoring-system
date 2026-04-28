package com.sipc.monitoringsystem.model.po.Environment;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
@TableName("environment_record")
public class EnvironmentRecord {
    @TableId(type = IdType.AUTO)
    private Integer id;

    private Integer monitorId;

    private String deviceCode;

    private String weather;

    private Float temperature;

    private Float humidity;

    private Float pm25;

    private Integer aqi;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT)
    private Timestamp createTime;
}
