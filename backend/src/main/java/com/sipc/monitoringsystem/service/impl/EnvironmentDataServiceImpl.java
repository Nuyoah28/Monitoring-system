package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.sipc.monitoringsystem.dao.EnvironmentRecordDao;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportEnvironmentParam;
import com.sipc.monitoringsystem.model.dto.param.weather.CreateWeatherParam;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.environment.EnvironmentTrendPointRes;
import com.sipc.monitoringsystem.model.po.Environment.EnvironmentRecord;
import com.sipc.monitoringsystem.service.EnvironmentDataService;
import com.sipc.monitoringsystem.service.WeatherService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class EnvironmentDataServiceImpl extends ServiceImpl<EnvironmentRecordDao, EnvironmentRecord> implements EnvironmentDataService {

    private final WeatherService weatherService;

    public EnvironmentDataServiceImpl(WeatherService weatherService) {
        this.weatherService = weatherService;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Integer report(ReportEnvironmentParam param) {
        EnvironmentRecord record = new EnvironmentRecord();
        record.setMonitorId(param.getMonitorId());
        record.setDeviceCode(param.getDeviceCode());
        record.setWeather(defaultWeather(param.getWeather()));
        record.setTemperature(defaultFloat(param.getTemperature(), 24F));
        record.setHumidity(defaultFloat(param.getHumidity(), 50F));
        record.setPm25(defaultFloat(param.getPm25(), 35F));
        record.setAqi(param.getAqi() == null ? 75 : param.getAqi());
        save(record);

        CreateWeatherParam weatherParam = new CreateWeatherParam();
        weatherParam.setMonitorId(record.getMonitorId());
        weatherParam.setWeather(record.getWeather());
        weatherParam.setTemperature(Math.round(record.getTemperature()));
        weatherParam.setHumidity(Math.round(record.getHumidity()));
        weatherService.addWeather(weatherParam);
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
        return record == null ? null : new EnvironmentRealtimeRes(record);
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
                    safeInt(item.getAqi()),
                    Math.round(defaultFloat(item.getHumidity(), 0F)),
                    Math.round(defaultFloat(item.getPm25(), 0F))
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
        entries.sort(Map.Entry.comparingByKey());
        int keep = "week".equals(range) ? 7 : 8;
        int fromIndex = Math.max(entries.size() - keep, 0);
        List<EnvironmentTrendPointRes> result = new ArrayList<>();
        for (Map.Entry<LocalDate, List<EnvironmentRecord>> entry : entries.subList(fromIndex, entries.size())) {
            List<EnvironmentRecord> dayRecords = entry.getValue();
            int size = Math.max(dayRecords.size(), 1);
            int avgAqi = Math.round((float) dayRecords.stream().map(EnvironmentRecord::getAqi).filter(v -> v != null).mapToInt(Integer::intValue).sum() / size);
            int avgHumidity = Math.round((float) dayRecords.stream().map(item -> defaultFloat(item.getHumidity(), 0F)).reduce(0F, Float::sum) / size);
            int avgPm25 = Math.round((float) dayRecords.stream().map(item -> defaultFloat(item.getPm25(), 0F)).reduce(0F, Float::sum) / size);
            String label = "week".equals(range)
                    ? entry.getKey().getMonthValue() + "/" + entry.getKey().getDayOfMonth()
                    : entry.getKey().getMonthValue() + "/" + String.format("%02d", entry.getKey().getDayOfMonth());
            result.add(new EnvironmentTrendPointRes(label, avgAqi, avgHumidity, avgPm25));
        }
        return result;
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

    private String defaultWeather(String weather) {
        return weather == null || weather.isBlank() ? "Sunny" : weather;
    }

    private Float defaultFloat(Float value, Float fallback) {
        return value == null ? fallback : value;
    }

    private Integer safeInt(Integer value) {
        return value == null ? 0 : value;
    }
}
