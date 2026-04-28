package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.sipc.monitoringsystem.dao.ParkingAreaRecordDao;
import com.sipc.monitoringsystem.dao.ParkingAreaStatusDao;
import com.sipc.monitoringsystem.model.dto.param.iot.ReportParkingParam;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingRealtimeRes;
import com.sipc.monitoringsystem.model.dto.res.parking.ParkingTrendPointRes;
import com.sipc.monitoringsystem.model.po.Parking.ParkingAreaRecord;
import com.sipc.monitoringsystem.model.po.Parking.ParkingAreaStatus;
import com.sipc.monitoringsystem.service.ParkingDataService;
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
import java.util.UUID;

@Slf4j
@Service
public class ParkingDataServiceImpl implements ParkingDataService {

    private final ParkingAreaStatusDao parkingAreaStatusDao;
    private final ParkingAreaRecordDao parkingAreaRecordDao;

    public ParkingDataServiceImpl(ParkingAreaStatusDao parkingAreaStatusDao, ParkingAreaRecordDao parkingAreaRecordDao) {
        this.parkingAreaStatusDao = parkingAreaStatusDao;
        this.parkingAreaRecordDao = parkingAreaRecordDao;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int report(ReportParkingParam param) {
        if (param.getZones() == null || param.getZones().isEmpty()) {
            return 0;
        }
        Timestamp now = new Timestamp(System.currentTimeMillis());
        String batchNo = UUID.randomUUID().toString().replace("-", "");
        int count = 0;
        for (ReportParkingParam.ZoneReport zone : param.getZones()) {
            String areaCode = defaultAreaCode(zone);
            ParkingAreaStatus status = parkingAreaStatusDao.selectOne(
                    new LambdaQueryWrapper<ParkingAreaStatus>()
                            .eq(ParkingAreaStatus::getMonitorId, param.getMonitorId())
                            .eq(ParkingAreaStatus::getAreaCode, areaCode)
                            .last("limit 1")
            );
            if (status == null) {
                status = new ParkingAreaStatus();
                status.setMonitorId(param.getMonitorId());
                status.setAreaCode(areaCode);
                status.setCreateTime(now);
            }
            status.setDeviceCode(param.getDeviceCode());
            status.setAreaName(defaultAreaName(zone));
            status.setTotalSpaces(Math.max(zone.getTotalSpaces() == null ? 0 : zone.getTotalSpaces(), 0));
            int occupied = Math.max(zone.getOccupiedSpaces() == null ? 0 : zone.getOccupiedSpaces(), 0);
            status.setOccupiedSpaces(Math.min(occupied, status.getTotalSpaces()));
            status.setUpdateTime(now);
            if (status.getId() == null) {
                parkingAreaStatusDao.insert(status);
            } else {
                parkingAreaStatusDao.updateById(status);
            }

            ParkingAreaRecord record = new ParkingAreaRecord();
            record.setMonitorId(param.getMonitorId());
            record.setDeviceCode(param.getDeviceCode());
            record.setBatchNo(batchNo);
            record.setAreaCode(status.getAreaCode());
            record.setAreaName(status.getAreaName());
            record.setTotalSpaces(status.getTotalSpaces());
            record.setOccupiedSpaces(status.getOccupiedSpaces());
            record.setCreateTime(now);
            parkingAreaRecordDao.insert(record);
            count++;
        }
        return count;
    }

    @Override
    public ParkingRealtimeRes getRealtime(Integer monitorId) {
        List<ParkingAreaStatus> zones = parkingAreaStatusDao.selectList(
                new LambdaQueryWrapper<ParkingAreaStatus>()
                        .eq(ParkingAreaStatus::getMonitorId, monitorId)
                        .orderByAsc(ParkingAreaStatus::getAreaName)
        );
        if (zones.isEmpty()) {
            return null;
        }
        ParkingRealtimeRes res = new ParkingRealtimeRes();
        res.setMonitorId(monitorId);
        res.setZones(new ArrayList<>());
        int total = 0;
        int used = 0;
        Timestamp latest = zones.stream()
                .map(ParkingAreaStatus::getUpdateTime)
                .filter(item -> item != null)
                .max(Comparator.naturalOrder())
                .orElse(null);
        for (ParkingAreaStatus zone : zones) {
            ParkingRealtimeRes.ZoneItem item = new ParkingRealtimeRes.ZoneItem();
            item.setAreaCode(zone.getAreaCode());
            item.setAreaName(zone.getAreaName());
            item.setTotalSpaces(zone.getTotalSpaces());
            item.setOccupiedSpaces(zone.getOccupiedSpaces());
            res.getZones().add(item);
            total += zone.getTotalSpaces() == null ? 0 : zone.getTotalSpaces();
            used += zone.getOccupiedSpaces() == null ? 0 : zone.getOccupiedSpaces();
        }
        res.setTotalSpaces(total);
        res.setOccupiedSpaces(used);
        res.setFreeSpaces(Math.max(total - used, 0));
        res.setOccupancyRate(total == 0 ? 0 : Math.round(used * 100F / total));
        res.setUpdateTime(latest);
        return res;
    }

    @Override
    public List<ParkingTrendPointRes> getTrend(Integer monitorId, String range) {
        String scopedRange = normalizeRange(range);
        List<ParkingAreaRecord> records = parkingAreaRecordDao.selectList(
                new LambdaQueryWrapper<ParkingAreaRecord>()
                        .eq(ParkingAreaRecord::getMonitorId, monitorId)
                        .ge(ParkingAreaRecord::getCreateTime, new Timestamp(resolveStartMillis(scopedRange)))
                        .orderByAsc(ParkingAreaRecord::getCreateTime)
        );
        if (records.isEmpty()) {
            return new ArrayList<>();
        }
        if ("day".equals(scopedRange)) {
            return buildDayTrend(records);
        }
        return buildDateAggregateTrend(records, scopedRange);
    }

    private List<ParkingTrendPointRes> buildDayTrend(List<ParkingAreaRecord> records) {
        Map<String, Snapshot> grouped = new LinkedHashMap<>();
        for (ParkingAreaRecord record : records) {
            String key = record.getBatchNo() == null ? String.valueOf(record.getCreateTime().getTime()) : record.getBatchNo();
            Snapshot snapshot = grouped.computeIfAbsent(key, ignored -> new Snapshot(record.getCreateTime()));
            snapshot.total += record.getTotalSpaces() == null ? 0 : record.getTotalSpaces();
            snapshot.used += record.getOccupiedSpaces() == null ? 0 : record.getOccupiedSpaces();
        }
        List<Snapshot> snapshots = new ArrayList<>(grouped.values());
        int fromIndex = Math.max(snapshots.size() - 24, 0);
        SimpleDateFormat format = new SimpleDateFormat("HH:mm");
        List<ParkingTrendPointRes> result = new ArrayList<>();
        for (Snapshot item : snapshots.subList(fromIndex, snapshots.size())) {
            int occupancy = item.total == 0 ? 0 : Math.round(item.used * 100F / item.total);
            result.add(new ParkingTrendPointRes(format.format(item.createTime), occupancy, item.used));
        }
        return result;
    }

    private List<ParkingTrendPointRes> buildDateAggregateTrend(List<ParkingAreaRecord> records, String range) {
        Map<LocalDate, List<ParkingAreaRecord>> grouped = new LinkedHashMap<>();
        for (ParkingAreaRecord item : records) {
            LocalDate date = Instant.ofEpochMilli(item.getCreateTime().getTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDate();
            grouped.computeIfAbsent(date, key -> new ArrayList<>()).add(item);
        }
        List<Map.Entry<LocalDate, List<ParkingAreaRecord>>> entries = new ArrayList<>(grouped.entrySet());
        entries.sort(Map.Entry.comparingByKey());
        int keep = "week".equals(range) ? 7 : 8;
        int fromIndex = Math.max(entries.size() - keep, 0);
        List<ParkingTrendPointRes> result = new ArrayList<>();
        for (Map.Entry<LocalDate, List<ParkingAreaRecord>> entry : entries.subList(fromIndex, entries.size())) {
            int total = entry.getValue().stream().map(ParkingAreaRecord::getTotalSpaces).filter(v -> v != null).mapToInt(Integer::intValue).sum();
            int used = entry.getValue().stream().map(ParkingAreaRecord::getOccupiedSpaces).filter(v -> v != null).mapToInt(Integer::intValue).sum();
            int occupancy = total == 0 ? 0 : Math.round(used * 100F / total);
            String label = entry.getKey().getMonthValue() + "/" + String.format("%02d", entry.getKey().getDayOfMonth());
            result.add(new ParkingTrendPointRes(label, occupancy, used));
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

    private String defaultAreaCode(ReportParkingParam.ZoneReport zone) {
        if (zone.getAreaCode() != null && !zone.getAreaCode().isBlank()) {
            return zone.getAreaCode();
        }
        return defaultAreaName(zone);
    }

    private String defaultAreaName(ReportParkingParam.ZoneReport zone) {
        return zone.getAreaName() == null || zone.getAreaName().isBlank() ? "Parking Area" : zone.getAreaName();
    }

    private static class Snapshot {
        private final Timestamp createTime;
        private int total;
        private int used;

        private Snapshot(Timestamp createTime) {
            this.createTime = createTime;
        }
    }
}
