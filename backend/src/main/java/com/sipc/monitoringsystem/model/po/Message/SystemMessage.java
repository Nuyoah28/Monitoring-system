package com.sipc.monitoringsystem.model.po.Message;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;

import static org.apache.ibatis.type.JdbcType.TIMESTAMP;

@TableName(value = "system_message")
@Data
public class SystemMessage {
    @TableId(type = IdType.AUTO)
    private Integer id;
    
    private String message;

    @TableField("receiver_user_id")
    private Integer receiverUserId;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @TableField(fill = FieldFill.INSERT,jdbcType = TIMESTAMP)
    private Timestamp timestamp;

    public Timestamp getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Timestamp timestamp) {
        this.timestamp = timestamp;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
