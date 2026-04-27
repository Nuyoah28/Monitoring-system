package com.sipc.monitoringsystem.model.po.Alarm;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

import static org.apache.ibatis.type.JdbcType.TIMESTAMP;

@Data
@TableName("alarm_push_record")
public class AlarmPushRecord {
    @TableId(type = IdType.AUTO)
    private Long id;

    private Integer alarmId;

    private Integer userId;

    private String pushType;

    private String pushStatus;

    private String pushDetail;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT, jdbcType = TIMESTAMP)
    private Timestamp createdTime;
}
