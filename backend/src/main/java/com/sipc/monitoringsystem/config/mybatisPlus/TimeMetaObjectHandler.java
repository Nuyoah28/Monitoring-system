package com.sipc.monitoringsystem.config.mybatisPlus;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

import java.sql.Timestamp;

/**
 * @author CZCZCZ
 * &#064;date  2023-08-04 17:47
 */
@Component
public class TimeMetaObjectHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        fillIfNull(metaObject, "createTime");
        fillIfNull(metaObject, "updateTime");
        fillIfNull(metaObject, "timestamp");
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.setFieldValByName("updateTime", new Timestamp(System.currentTimeMillis()), metaObject);
    }

    private void fillIfNull(MetaObject metaObject, String fieldName) {
        if (metaObject.hasSetter(fieldName) && this.getFieldValByName(fieldName, metaObject) == null) {
            this.setFieldValByName(fieldName, new Timestamp(System.currentTimeMillis()), metaObject);
        }
    }
}
