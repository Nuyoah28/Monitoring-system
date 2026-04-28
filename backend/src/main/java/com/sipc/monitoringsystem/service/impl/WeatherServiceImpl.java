package com.sipc.monitoringsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sipc.monitoringsystem.dao.WeatherDao;
import com.sipc.monitoringsystem.dao.WeatherRegionConfigDao;
import com.sipc.monitoringsystem.model.dto.param.weather.CreateWeatherParam;
import com.sipc.monitoringsystem.model.dto.res.Weather.WeatherForecastDayRes;
import com.sipc.monitoringsystem.model.po.Monitor.Monitor;
import com.sipc.monitoringsystem.model.po.Weather.Weather;
import com.sipc.monitoringsystem.model.po.Weather.WeatherRegionConfig;
import com.sipc.monitoringsystem.service.MonitorService;
import com.sipc.monitoringsystem.service.WeatherService;
import com.sipc.monitoringsystem.util.HttpUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class WeatherServiceImpl extends ServiceImpl<WeatherDao, Weather> implements WeatherService {

    private static final long WEATHER_CACHE_MILLIS = 20 * 60 * 1000L;
    private static final String GEOCODE_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search";
    private static final String FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast";

    private final WeatherRegionConfigDao weatherRegionConfigDao;
    private final MonitorService monitorService;
    private final ObjectMapper objectMapper;

    public WeatherServiceImpl(WeatherRegionConfigDao weatherRegionConfigDao,
                              MonitorService monitorService,
                              ObjectMapper objectMapper) {
        this.weatherRegionConfigDao = weatherRegionConfigDao;
        this.monitorService = monitorService;
        this.objectMapper = objectMapper;
    }

    @Override
    @Cacheable(value = "cache", key = "'getNewestWeatherByMonitorId_'+#monitorId", unless = "#result==null")
    public Weather getNewestWeatherByMonitorId(Integer monitorId) {
        Weather latest = findLatestWeather(monitorId);
        if (isWeatherFresh(latest)) {
            return latest;
        }
        Weather synced = syncWeatherByMonitorId(monitorId);
        return synced != null ? synced : latest;
    }

    @Override
    @Cacheable(value = "cache", key = "'getWeatherListByMonitorId_'+#monitorId", unless = "#result==null")
    public List<Weather> getWeatherListByMonitorId(Integer monitorId) {
        return list(
                new LambdaQueryWrapper<Weather>()
                        .eq(Weather::getMonitorId, monitorId)
                        .orderByDesc(Weather::getCreateTime)
        );
    }

    @Override
    @CacheEvict(value = "cache", allEntries = true)
    public Integer addWeather(CreateWeatherParam param) {
        Weather weather = new Weather();
        weather.setMonitorId(param.getMonitorId());
        weather.setWeather(param.getWeather());
        weather.setTemperature(param.getTemperature());
        weather.setHumidity(param.getHumidity());
        weather.setSource("manual");
        try {
            save(weather);
            return weather.getId();
        } catch (Exception e) {
            log.error("addWeather failed", e);
            return -1;
        }
    }

    @Override
    @CacheEvict(value = "cache", allEntries = true)
    public Weather syncWeatherByMonitorId(Integer monitorId) {
        try {
            WeatherRegionConfig config = resolveRegionConfig(monitorId);
            if (config == null || config.getLatitude() == null || config.getLongitude() == null) {
                log.warn("weather sync skipped, region config missing for monitor {}", monitorId);
                return null;
            }

            String url = FORECAST_ENDPOINT
                    + "?latitude=" + config.getLatitude()
                    + "&longitude=" + config.getLongitude()
                    + "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
                    + "&timezone=auto&forecast_days=3";
            String response = HttpUtils.get(url);
            if (response == null || response.isBlank()) {
                return null;
            }

            JsonNode root = objectMapper.readTree(response);
            JsonNode current = root.path("current");
            if (current.isMissingNode() || current.isNull()) {
                return null;
            }

            Weather weather = new Weather();
            weather.setMonitorId(monitorId);
            weather.setRegionName(config.getRegionName());
            weather.setLatitude(config.getLatitude());
            weather.setLongitude(config.getLongitude());
            weather.setTemperature((float) current.path("temperature_2m").asDouble(0D));
            weather.setHumidity((float) current.path("relative_humidity_2m").asDouble(0D));
            weather.setWeatherCode(current.path("weather_code").asInt(0));
            weather.setWeather(mapWeatherText(weather.getWeatherCode()));
            weather.setWindSpeed((float) current.path("wind_speed_10m").asDouble(0D));
            weather.setSource("open-meteo");
            save(weather);
            return weather;
        } catch (Exception e) {
            log.error("syncWeatherByMonitorId failed, monitorId={}", monitorId, e);
            return null;
        }
    }

    @Override
    public List<WeatherForecastDayRes> getForecastByMonitorId(Integer monitorId) {
        try {
            WeatherRegionConfig config = resolveRegionConfig(monitorId);
            if (config == null || config.getLatitude() == null || config.getLongitude() == null) {
                return new ArrayList<>();
            }

            String url = FORECAST_ENDPOINT
                    + "?latitude=" + config.getLatitude()
                    + "&longitude=" + config.getLongitude()
                    + "&daily=weather_code,temperature_2m_max,temperature_2m_min"
                    + "&timezone=auto&forecast_days=3";
            String response = HttpUtils.get(url);
            if (response == null || response.isBlank()) {
                return new ArrayList<>();
            }

            JsonNode root = objectMapper.readTree(response);
            JsonNode daily = root.path("daily");
            JsonNode dates = daily.path("time");
            JsonNode weatherCodes = daily.path("weather_code");
            JsonNode maxTemps = daily.path("temperature_2m_max");
            JsonNode minTemps = daily.path("temperature_2m_min");

            List<WeatherForecastDayRes> result = new ArrayList<>();
            for (int i = 0; i < dates.size(); i++) {
                result.add(new WeatherForecastDayRes(
                        dates.path(i).asText(""),
                        mapWeatherText(weatherCodes.path(i).asInt(0)),
                        String.valueOf(Math.round(maxTemps.path(i).asDouble(0D))),
                        String.valueOf(Math.round(minTemps.path(i).asDouble(0D)))
                ));
            }
            return result;
        } catch (Exception e) {
            log.error("getForecastByMonitorId failed, monitorId={}", monitorId, e);
            return new ArrayList<>();
        }
    }

    private Weather findLatestWeather(Integer monitorId) {
        return getOne(
                new LambdaQueryWrapper<Weather>()
                        .eq(Weather::getMonitorId, monitorId)
                        .orderByDesc(Weather::getCreateTime)
                        .last("limit 1")
        );
    }

    private boolean isWeatherFresh(Weather weather) {
        if (weather == null || weather.getCreateTime() == null) {
            return false;
        }
        long age = System.currentTimeMillis() - weather.getCreateTime().getTime();
        return age <= WEATHER_CACHE_MILLIS;
    }

    private WeatherRegionConfig resolveRegionConfig(Integer monitorId) throws Exception {
        WeatherRegionConfig config = weatherRegionConfigDao.selectOne(
                new LambdaQueryWrapper<WeatherRegionConfig>()
                        .eq(WeatherRegionConfig::getMonitorId, monitorId)
                        .last("limit 1")
        );
        if (config != null && config.getLatitude() != null && config.getLongitude() != null) {
            return config;
        }

        Monitor monitor = monitorService.getMonitorById(monitorId);
        if (monitor == null) {
            return null;
        }

        String regionKeyword = monitor.getArea();
        if (regionKeyword == null || regionKeyword.isBlank()) {
            regionKeyword = monitor.getName();
        }
        if (regionKeyword == null || regionKeyword.isBlank()) {
            return null;
        }

        String url = GEOCODE_ENDPOINT
                + "?name=" + URLEncoder.encode(regionKeyword, StandardCharsets.UTF_8)
                + "&count=1&language=zh&format=json";
        String response = HttpUtils.get(url);
        if (response == null || response.isBlank()) {
            return config;
        }

        JsonNode root = objectMapper.readTree(response);
        JsonNode first = root.path("results").path(0);
        if (first.isMissingNode() || first.isNull()) {
            return config;
        }

        WeatherRegionConfig target = config == null ? new WeatherRegionConfig() : config;
        target.setMonitorId(monitorId);
        target.setRegionName(first.path("name").asText(regionKeyword));
        target.setLatitude(first.path("latitude").asDouble());
        target.setLongitude(first.path("longitude").asDouble());
        target.setTimezone(first.path("timezone").asText("Asia/Shanghai"));
        target.setEnabled(1);

        if (target.getId() == null) {
            weatherRegionConfigDao.insert(target);
        } else {
            weatherRegionConfigDao.updateById(target);
        }
        return target;
    }

    private String mapWeatherText(int code) {
        return switch (code) {
            case 0 -> "晴";
            case 1, 2 -> "多云";
            case 3 -> "阴";
            case 45, 48 -> "雾";
            case 51, 53, 55, 56, 57 -> "毛毛雨";
            case 61, 63, 65, 66, 67, 80, 81, 82 -> "雨";
            case 71, 73, 75, 77, 85, 86 -> "雪";
            case 95, 96, 99 -> "雷阵雨";
            default -> "未知";
        };
    }
}
