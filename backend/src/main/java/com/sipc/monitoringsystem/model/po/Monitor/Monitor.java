package com.sipc.monitoringsystem.model.po.Monitor;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName(value = "monitor")
public class Monitor {
    @TableId(type = IdType.AUTO)
    private Integer id;
    private String name;
    private String area;
    private String leader;
    private Integer alarmCnt;
    private String streamLink;
    private Boolean dangerArea;
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
