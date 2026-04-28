package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.EnvironmentRecordDao;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportEnvironmentParam;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentTrendPointRes;
import com.sipc.monitoringsystem.model.po.Environment.EnvironmentRecord;
import com.sipc.monitoringsystem.service.EnvironmentDataService;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class EnvironmentDataServiceImpl extends ServiceImpl<EnvironmentRecordDao, EnvironmentRecord> implements EnvironmentDataService {

    @Override
    public Integer report(ReportEnvironmentParam param) {
        EnvironmentRecord record = new EnvironmentRecord();
        record.setMonitorId(param.getMonitorId());
        record.setDeviceCode(param.getDeviceCode());
        record.setTemperature(defaultFloat(param.getTemperature(), 24F));
        record.setHumidity(defaultFloat(param.getHumidity(), 50F));
        record.setPm25(defaultFloat(param.getPm25(), 35F));
        record.setCombustibleGas(defaultFloat(param.getCombustibleGas(), 0F));
        save(record);
        return record.getId();
    }

    @Override
    public EnvironmentRealtimeRes getRealtime(Integer monitorId) {
        EnvironmentRecord record = getOne(
                new LambdaQueryWrapper<EnvironmentRecord>()
                        .eq(EnvironmentRecord::getMonitorId, monitorId)
                        .orderByDesc(EnvironmentRecord::getCreateTime)
                        .last("limit 1")
        );
        if (record == null) {
            return null;
        }
        EnvironmentRealtimeRes res = new EnvironmentRealtimeRes(record);
        res.setAqi(pm25ToAqi(record.getPm25()));
        return res;
    }

    @Override
    public List<EnvironmentTrendPointRes> getTrend(Integer monitorId, String range) {
        String scopedRange = normalizeRange(range);
        List<EnvironmentRecord> records = list(
                new LambdaQueryWrapper<EnvironmentRecord>()
                        .eq(EnvironmentRecord::getMonitorId, monitorId)
                        .ge(EnvironmentRecord::getCreateTime, new Timestamp(resolveStartMillis(scopedRange)))
                        .orderByAsc(EnvironmentRecord::getCreateTime)
        );
        if (records.isEmpty()) {
            return new ArrayList<>();
        }
        if ("day".equals(scopedRange)) {
            return buildDayTrend(records);
        }
        return buildDateAggregateTrend(records, scopedRange);
    }

    private List<EnvironmentTrendPointRes> buildDayTrend(List<EnvironmentRecord> records) {
        int fromIndex = Math.max(records.size() - 24, 0);
        List<EnvironmentRecord> sliced = records.subList(fromIndex, records.size());
        SimpleDateFormat format = new SimpleDateFormat("HH:mm");
        List<EnvironmentTrendPointRes> result = new ArrayList<>();
        for (EnvironmentRecord item : sliced) {
            result.add(new EnvironmentTrendPointRes(
                    format.format(item.getCreateTime()),
                    pm25ToAqi(item.getPm25()),
                    Math.round(defaultFloat(item.getHumidity(), 0F)),
                    Math.round(defaultFloat(item.getPm25(), 0F)),
                    Math.round(defaultFloat(item.getCombustibleGas(), 0F))
            ));
        }
        return result;
    }

    private List<EnvironmentTrendPointRes> buildDateAggregateTrend(List<EnvironmentRecord> records, String range) {
        Map<LocalDate, List<EnvironmentRecord>> grouped = new LinkedHashMap<>();
        for (EnvironmentRecord item : records) {
            LocalDate date = Instant.ofEpochMilli(item.getCreateTime().getTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDate();
            grouped.computeIfAbsent(date, key -> new ArrayList<>()).add(item);
        }
        List<Map.Entry<LocalDate, List<EnvironmentRecord>>> entries = new ArrayList<>(grouped.entrySet());
        int keep = "week".equals(range) ? 7 : 8;
        int fromIndex = Math.max(entries.size() - keep, 0);
        List<EnvironmentTrendPointRes> result = new ArrayList<>();
        for (Map.Entry<LocalDate, List<EnvironmentRecord>> entry : entries.subList(fromIndex, entries.size())) {
            List<EnvironmentRecord> dayRecords = entry.getValue();
            int size = Math.max(dayRecords.size(), 1);
            float avgHumidity = sumHumidity(dayRecords) / size;
            float avgPm25 = sumPm25(dayRecords) / size;
            float avgGas = sumGas(dayRecords) / size;
            String label = "week".equals(range)
                    ? entry.getKey().getMonthValue() + "/" + entry.getKey().getDayOfMonth()
                    : entry.getKey().getMonthValue() + "/" + String.format("%02d", entry.getKey().getDayOfMonth());
            result.add(new EnvironmentTrendPointRes(
                    label,
                    pm25ToAqi(avgPm25),
                    Math.round(avgHumidity),
                    Math.round(avgPm25),
                    Math.round(avgGas)
            ));
        }
        return result;
    }

    private float sumHumidity(List<EnvironmentRecord> records) {
        float sum = 0F;
        for (EnvironmentRecord item : records) {
            sum += defaultFloat(item.getHumidity(), 0F);
        }
        return sum;
    }

    private float sumPm25(List<EnvironmentRecord> records) {
        float sum = 0F;
        for (EnvironmentRecord item : records) {
            sum += defaultFloat(item.getPm25(), 0F);
        }
        return sum;
    }

    private float sumGas(List<EnvironmentRecord> records) {
        float sum = 0F;
        for (EnvironmentRecord item : records) {
            sum += defaultFloat(item.getCombustibleGas(), 0F);
        }
        return sum;
    }

    private int pm25ToAqi(Float pm25Raw) {
        float pm25 = defaultFloat(pm25Raw, 0F);
        if (pm25 <= 12.0F) return calcAqi(pm25, 0F, 12.0F, 0, 50);
        if (pm25 <= 35.4F) return calcAqi(pm25, 12.1F, 35.4F, 51, 100);
        if (pm25 <= 55.4F) return calcAqi(pm25, 35.5F, 55.4F, 101, 150);
        if (pm25 <= 150.4F) return calcAqi(pm25, 55.5F, 150.4F, 151, 200);
        if (pm25 <= 250.4F) return calcAqi(pm25, 150.5F, 250.4F, 201, 300);
        return calcAqi(pm25, 250.5F, 500.4F, 301, 500);
    }

    private int calcAqi(float value, float cLow, float cHigh, int iLow, int iHigh) {
        return Math.round((iHigh - iLow) * (value - cLow) / (cHigh - cLow) + iLow);
    }

    private long resolveStartMillis(String range) {
        long now = System.currentTimeMillis();
        if ("week".equals(range)) {
            return now - 7L * 24 * 60 * 60 * 1000;
        }
        if ("month".equals(range)) {
            return now - 30L * 24 * 60 * 60 * 1000;
        }
        return now - 24L * 60 * 60 * 1000;
    }

    private String normalizeRange(String range) {
        if ("week".equalsIgnoreCase(range) || "month".equalsIgnoreCase(range)) {
            return range.toLowerCase();
        }
        return "day";
    }

    private Float defaultFloat(Float value, Float fallback) {
        return value == null ? fallback : value;
    }
}
