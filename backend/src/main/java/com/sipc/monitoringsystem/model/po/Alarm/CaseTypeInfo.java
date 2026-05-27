package com.sipc.monitoringsystem.model.po.Alarm;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName(value = "case_type_info")
public class CaseTypeInfo
{
    private Integer id;
    private String caseTypeName;
    private Integer warningLevel;
    private Boolean enabled;
}
