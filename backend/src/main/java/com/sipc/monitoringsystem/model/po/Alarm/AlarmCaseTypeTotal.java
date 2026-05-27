package com.sipc.monitoringsystem.model.po.Alarm;

import lombok.Data;

@Data
public class AlarmCaseTypeTotal
{
    private String caseTypeName;

    private Integer todayNew;

    private Integer total;


}
