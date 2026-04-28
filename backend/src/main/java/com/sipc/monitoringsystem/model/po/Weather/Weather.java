package com.sipc.monitoringsystem.model.po.Weather;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

import static org.apache.ibatis.type.JdbcType.TIMESTAMP;

@Data
@TableName("weather_info")
public class Weather {
        private Integer id;
        private Integer monitorId;
        private String regionName;
        private String weather;
        private Integer weatherCode;
        private float temperature;
        private float humidity;
        private float windSpeed;
        private Double latitude;
        private Double longitude;
        private String source;
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        @TableField(fill = FieldFill.INSERT,jdbcType = TIMESTAMP)
        private Timestamp createTime;//
}
