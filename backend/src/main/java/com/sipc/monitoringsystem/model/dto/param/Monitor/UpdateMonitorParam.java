package com.sipc.monitoringsystem.model.dto.param.Monitor;

import lombok.Data;

/**
 * @author CZCZCZ
 * &#064;date 2023-10-03 14:37
 */

@Data
public class UpdateMonitorParam {
    //TODO 改字段要改这里
    private Integer id;
    private String name;
    private String area;
    private String leader;
    private Boolean running;
    private Boolean fall;
    private Boolean flame;
    private Boolean smoke;
    private Boolean punch;
    private Boolean rubbish;
    private Boolean ice;
    private Boolean ebike;
    private Boolean vehicle;
    private Boolean wave;
    private Integer leftX;
    private Integer leftY;
    private Integer rightX;
    private Integer rightY;
}
