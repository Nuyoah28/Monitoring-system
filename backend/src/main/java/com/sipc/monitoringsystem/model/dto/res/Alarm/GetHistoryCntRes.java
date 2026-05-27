package com.sipc.monitoringsystem.model.dto.res.Alarm;

import com.sipc.monitoringsystem.model.po.Alarm.TimePeriod;
import lombok.Data;

import java.util.List;


@Data
public class GetHistoryCntRes
{
    List<TimePeriod> graph1;

    List<TimePeriod> graph2;

    List<TimePeriod> graph3;

}
