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
@TableName("parking_traffic_flow_record")
public class ParkingTrafficFlowRecord {
    @TableId(type = IdType.AUTO)
    private Integer id;

    private Integer monitorId;

    private String deviceCode;

    private String batchNo;

    private Integer inCount;

    private Integer outCount;

    private Integer netFlow;

    private Integer totalFlow;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT)
    private Timestamp createTime;
}
