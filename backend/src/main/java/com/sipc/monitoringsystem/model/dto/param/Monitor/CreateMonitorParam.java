package com.sipc.monitoringsystem.model.dto.param.Monitor;

import lombok.Data;


@Data
public class CreateMonitorParam
{
    private String name;
    private String area;
    private String leader;
    private String ip;
    private Integer leftX;
    private Integer leftY;
    private Integer rightX;
    private Integer rightY;
}
