package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface VisitorDao extends BaseMapper<VisitorInfo> {
}
