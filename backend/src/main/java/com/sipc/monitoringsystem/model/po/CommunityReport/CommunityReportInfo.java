package com.sipc.monitoringsystem.model.po.CommunityReport;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.sql.Timestamp;
import java.util.List;

@Data
@TableName("community_report")
public class CommunityReportInfo {
    @TableId(type = IdType.AUTO)
    private Integer id;

    private String category;

    private String description;

    private String location;

    /** 图片 COS objectKey 列表，逗号分隔存储 */
    @TableField("image_keys")
    private String imageKeys;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField("report_time")
    private Timestamp reportTime;

    /** 处理状态：0待处理 1处理中 2已处理 */
    private Integer status;

    @TableField("handle_reply")
    private String handleReply;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    @TableField("handle_time")
    private Timestamp handleTime;

    private String handler;

    private String publisher;

    @TableField("owner_user_id")
    private Integer ownerUserId;

    /** 非持久化派生字段：image_keys 拼成完整 COS 访问 URL 列表，仅用于返回前端 */
    @TableField(exist = false)
    private List<String> imageUrls;
}
