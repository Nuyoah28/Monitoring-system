package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;
import com.sipc.monitoringsystem.model.po.User.User;

import java.util.List;

public interface VisitorService {
    List<VisitorInfo> listAll(User currentUser);

    VisitorInfo getById(Integer id, User currentUser);

    Integer create(VisitorInfo info, User currentUser);

    boolean update(VisitorInfo info, User currentUser);

    boolean delete(Integer id, User currentUser);
}
