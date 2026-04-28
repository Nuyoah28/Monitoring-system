#include "network.h"
#include <curl/curl.h>
#include <string>
#include <iostream>
#include <sstream>
#include <thread>
#include <chrono>
#include <atomic>
#include <cstdlib>
#include <ctime>
#include <vector>

static std::atomic<bool> weather_monitoring_active(false);
static std::thread weather_thread;

static const std::string kServerIp = []() {
    const char* ip = std::getenv("SERVER_IP");
    return ip ? std::string(ip) : std::string("192.168.213.197");
}();

static const int kJavaPort = []() {
    const char* port = std::getenv("JAVA_PORT");
    return port ? std::atoi(port) : 10215;
}();

struct ParkingZoneState {
    std::string area_code;
    std::string area_name;
    int total_spaces;
    int occupied_spaces;
};

static std::vector<ParkingZoneState> parking_zones = {
    {"garage_a", "Garage-A", 62, 36},
    {"garage_b", "Garage-B", 44, 24},
    {"east_ground", "East-Ground", 30, 15},
    {"west_ground", "West-Ground", 24, 10},
};

static std::string makeUrl(const std::string& path) {
    std::ostringstream oss;
    oss << "http://" << kServerIp << ':' << kJavaPort << path;
    return oss.str();
}

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    size_t totalSize = size * nmemb;
    userp->append((char*)contents, totalSize);
    return totalSize;
}

static int getTemperature() {
    return rand() % 10 + 20;
}

static int getHumidity() {
    return rand() % 20 + 40;
}

static int getPm25() {
    return rand() % 50 + 18;
}

static int getCombustibleGas() {
    return rand() % 35 + 5;
}

void triggerAlarm() {
    CURL* curl;
    CURLcode res;
    std::string response_data;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        std::string url = makeUrl("/api/v1/monitor-device/alarm");
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, "Authorization: sipc115");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        std::string postData = "{}";
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, postData.length());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "triggerAlarm curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Alarm triggered. Response code: " << response_code << std::endl;
            std::cout << "Response: " << response_data << std::endl;
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
}

void sendWeatherData(int temperature, int humidity) {
    CURL* curl;
    CURLcode res;
    std::string response_data;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        std::string url = makeUrl("/api/v1/iot/environment/report");
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        const int pm25 = getPm25();
        const int combustibleGas = getCombustibleGas();
        std::ostringstream jsonStream;
        jsonStream << "{";
        jsonStream << "\"monitorId\": 1,";
        jsonStream << "\"deviceCode\": \"iot-simulator-01\",";
        jsonStream << "\"temperature\":" << temperature << ",";
        jsonStream << "\"humidity\":" << humidity << ",";
        jsonStream << "\"pm25\":" << pm25 << ",";
        jsonStream << "\"combustibleGas\":" << combustibleGas;
        jsonStream << "}";

        std::string postData = jsonStream.str();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, postData.length());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "sendWeatherData curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Environment data sent. Response code: " << response_code << std::endl;
            std::cout << "Response: " << response_data << std::endl;
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
}

void sendParkingData() {
    CURL* curl;
    CURLcode res;
    std::string response_data;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        std::string url = makeUrl("/api/v1/iot/parking/report");
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        const std::time_t now = std::time(nullptr);
        const std::tm* local_time = std::localtime(&now);
        const int hour = local_time ? local_time->tm_hour : 12;
        const int traffic_bias = ((hour >= 7 && hour <= 10) || (hour >= 17 && hour <= 21)) ? 1 : -1;

        for (auto& zone : parking_zones) {
            int delta = (rand() % 5) - 2 + traffic_bias;
            int next_occupied = zone.occupied_spaces + delta;
            if (next_occupied < 0) next_occupied = 0;
            if (next_occupied > zone.total_spaces) next_occupied = zone.total_spaces;
            zone.occupied_spaces = next_occupied;
        }

        std::ostringstream jsonStream;
        jsonStream << "{";
        jsonStream << "\"monitorId\": 1,";
        jsonStream << "\"deviceCode\": \"iot-simulator-01\",";
        jsonStream << "\"zones\": [";
        for (size_t i = 0; i < parking_zones.size(); ++i) {
            const auto& zone = parking_zones[i];
            if (i > 0) jsonStream << ",";
            jsonStream << "{";
            jsonStream << "\"areaCode\": \"" << zone.area_code << "\",";
            jsonStream << "\"areaName\": \"" << zone.area_name << "\",";
            jsonStream << "\"totalSpaces\": " << zone.total_spaces << ",";
            jsonStream << "\"occupiedSpaces\": " << zone.occupied_spaces;
            jsonStream << "}";
        }
        jsonStream << "]";
        jsonStream << "}";

        std::string postData = jsonStream.str();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, postData.length());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "sendParkingData curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Parking data sent. Response code: " << response_code << std::endl;
            std::cout << "Response: " << response_data << std::endl;
        }

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
}

static void weatherMonitoringLoop(int initial_temperature, int initial_humidity) {
    sendWeatherData(initial_temperature, initial_humidity);
    sendParkingData();

    while (weather_monitoring_active.load()) {
        for (int i = 0; i < 120 && weather_monitoring_active.load(); i++) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }

        if (!weather_monitoring_active.load()) {
            break;
        }

        int temp = getTemperature();
        int hum = getHumidity();
        sendWeatherData(temp, hum);
        sendParkingData();
    }
}

void startWeatherMonitoring(int initial_temperature, int initial_humidity) {
    if (weather_monitoring_active.load()) {
        std::cout << "Weather monitoring is already running." << std::endl;
        return;
    }

    weather_monitoring_active.store(true);
    srand(static_cast<unsigned int>(time(nullptr)));
    weather_thread = std::thread(weatherMonitoringLoop, initial_temperature, initial_humidity);
    std::cout << "Weather monitoring started. Will send data every 2 minutes." << std::endl;
}

void stopWeatherMonitoring() {
    if (!weather_monitoring_active.load()) {
        std::cout << "Weather monitoring is not running." << std::endl;
        return;
    }

    weather_monitoring_active.store(false);
    if (weather_thread.joinable()) {
        weather_thread.join();
    }

    std::cout << "Weather monitoring stopped." << std::endl;
}
