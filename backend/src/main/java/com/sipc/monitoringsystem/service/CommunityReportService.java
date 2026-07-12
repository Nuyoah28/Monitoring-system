package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.CommunityReport.CommunityReportInfo;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.List;

public interface CommunityReportService {
    List<CommunityReportInfo> listForUser(User currentUser);

    CommunityReportInfo getById(Integer id, User currentUser);

    Integer create(CommunityReportInfo info, User currentUser);

    boolean handle(Integer id, Integer status, String reply, User currentUser);

    boolean delete(Integer id, User currentUser);
}
