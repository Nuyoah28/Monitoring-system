package com.sipc.monitoringsystem.model.po.Monitor;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

@Data
@TableName("monitor_recognition_rule")
public class MonitorRecognitionRule {
    @TableId(type = IdType.AUTO)
    private Long id;

    private Integer monitorId;

    private String name;

    private String prompt;

    private String translatedPrompt;

    private Integer riskLevel;

    private String alertHint;

    private Boolean enabled;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT)
    private Timestamp createTime;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Timestamp updateTime;
}
