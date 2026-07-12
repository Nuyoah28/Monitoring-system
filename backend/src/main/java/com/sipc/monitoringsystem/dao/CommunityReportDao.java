package com.sipc.monitoringsystem.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.sipc.monitoringsystem.model.po.CommunityReport.CommunityReportInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CommunityReportDao extends BaseMapper<CommunityReportInfo> {
}
