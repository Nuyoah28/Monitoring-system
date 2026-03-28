package com.sipc.monitoringsystem.model.po.Parking;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("parking_space_info")
public class ParkingSpaceInfo {
    @TableId(type = IdType.AUTO)
    private Integer id;

    private String location;

    @TableField("occupied_vehicle")
    private String occupiedVehicle;

    @TableField("total_spaces")
    private Integer totalSpaces;

    public Integer getId() {
        return id;
    }
}
