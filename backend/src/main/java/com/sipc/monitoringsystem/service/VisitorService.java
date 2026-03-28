package com.sipc.monitoringsystem.service;

import com.sipc.monitoringsystem.model.po.Visitor.VisitorInfo;

import java.util.List;

public interface VisitorService {
    List<VisitorInfo> listAll();

    VisitorInfo getById(Integer id);

    Integer create(VisitorInfo info);

    boolean update(VisitorInfo info);

    boolean delete(Integer id);
}
