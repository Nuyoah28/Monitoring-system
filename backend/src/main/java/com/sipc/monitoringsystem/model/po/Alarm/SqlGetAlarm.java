package com.sipc.monitoringsystem.model.po.Alarm;

import lombok.Data;

import java.sql.Timestamp;

/**
 * @author CZCZCZ
 *         &#064;date 2023-09-13 17:53
 */
@Data
public class SqlGetAlarm {

    private Integer id;
    private Integer caseType;
    private Integer monitorId; // 新增：监控ID，用于权限过滤
    private String clipLink;
    private String name;
    private String caseTypeName;
    private Integer warningLevel;
    private Timestamp createTime;
    private Boolean status;
    private String processingContent;
    private String area;
    private String phone;

}
