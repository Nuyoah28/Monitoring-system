package com.sipc.monitoringsystem.model.dto.param.alarm;

import jakarta.validation.constraints.NotNull;
import lombok.Data;


@Data
public class UpdateAlarmParam {

    @NotNull(message = "id不能为空")
    private Integer id;

    @NotNull(message = "status不能为空")
    private Boolean status;


    @NotNull(message = "processingContent不能为空")
    private String processingContent;

}
