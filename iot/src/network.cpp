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

// 全局变量用于控制天气监测线程
static std::atomic<bool> weather_monitoring_active(false);
static std::thread weather_thread;

// ==== network configuration ====
// 默认使用开发阶段服务器地址和端口，可以通过环境变量覆盖。
static const std::string kServerIp = [](){
    const char* ip = std::getenv("SERVER_IP");
    return ip ? std::string(ip) : std::string("192.168.213.197");
}();
static const int kJavaPort = [](){
    const char* port = std::getenv("JAVA_PORT");
    return port ? std::atoi(port) : 10215;
}();
static const int kRtmpPort = [](){
    const char* port = std::getenv("RTMP_PORT");
    return port ? std::atoi(port) : 1935;
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

// helper to build full URL
static std::string makeUrl(const std::string &path) {
    std::ostringstream oss;
    oss << "http://" << kServerIp << ':' << kJavaPort << path;
    return oss.str();
}


// 回调函数用于处理HTTP响应
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    size_t totalSize = size * nmemb;
    userp->append((char*)contents, totalSize);
    return totalSize;
}

static std::string randomWeather() {
    static const std::vector<std::string> weather_list = {
        "Sunny", "Cloudy", "Light Rain", "Overcast"
    };
    return weather_list[static_cast<size_t>(rand()) % weather_list.size()];
}

static int getPm25() {
    return rand() % 50 + 18;
}

static int getAqi() {
    return rand() % 65 + 55;
}

void triggerAlarm() {
    CURL* curl;
    CURLcode res;
    std::string response_data;

    // 初始化libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if(curl) {
        // 设置POST请求的URL (开发服务器IP/端口可通过环境变量 SERVER_IP/ JAVA_PORT 覆盖)
        std::string url = makeUrl("/api/v1/monitor-device/alarm");
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());

        // 设置POST方法
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        // 设置请求头
        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, "Authorization: sipc115");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // 设置POST数据 - 空JSON对象
        std::string postData = "{}";
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, postData.length());

        // 设置响应回调函数
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

        // 执行请求
        res = curl_easy_perform(curl);

        // 检查请求是否成功
        if(res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Alarm triggered. Response code: " << response_code << std::endl;
            std::cout << "Response: " << response_data << std::endl;
        }

        // 清理
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
}

void sendWeatherData(int temperature, int humidity) {
    CURL* curl;
    CURLcode res;
    std::string response_data;

    // 初始化libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if(curl) {
        // 设置POST请求的URL (使用与报警相同的Java后端地址)
        std::string url = makeUrl("/api/v1/weather/add");
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());

        // 设置POST方法
        curl_easy_setopt(curl, CURLOPT_POST, 1L);

        // 设置请求头（无认证）
        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // 构建POST数据，按照CreateWeatherParam类的要求
        std::ostringstream jsonStream;
        jsonStream << "{";
        jsonStream << "\"monitorId\": 1,";
        jsonStream << "\"weather\": \"多云\",";
        jsonStream << "\"temperature\":" << temperature << ",";
        jsonStream << "\"humidity\":" << humidity;
        jsonStream << "}";

        std::string postData = jsonStream.str();
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, postData.length());

        // 设置响应回调函数
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_data);

        // 执行请求
        res = curl_easy_perform(curl);

        // 检查请求是否成功
        if(res != CURLE_OK) {
            std::cerr << "sendWeatherData curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        } else {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            std::cout << "Weather data sent. Response code: " << response_code << std::endl;
            std::cout << "Response: " << response_data << std::endl;
        }

        // 清理
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }

    curl_global_cleanup();
}

// 模拟获取传感器数据的函数
int getTemperature() {
    // 模拟温度传感器数据 - 实际应用中应从硬件读取
    return rand() % 10 + 20; // 返回20-30之间的随机温度值
}

int getHumidity() {
    // 模拟湿度传感器数据 - 实际应用中应从硬件读取
    return rand() % 20 + 40; // 返回40-60之间的随机湿度值
}

// 定时发送天气数据的线程函数
void weatherMonitoringLoop(int initial_temperature, int initial_humidity) {
    // 使用初始值发送第一次数据
    sendWeatherData(initial_temperature, initial_humidity);
    
    while(weather_monitoring_active.load()) {
        // 等待2分钟 (120秒)
        for(int i = 0; i < 120 && weather_monitoring_active.load(); i++) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
        
        // 检查是否仍需继续运行
        if(!weather_monitoring_active.load()) {
            break;
        }
        
        // 从模拟传感器获取新数据并发送
        int temp = getTemperature();
        int hum = getHumidity();
        sendWeatherData(temp, hum);
    }
}

void startWeatherMonitoring(int initial_temperature, int initial_humidity) {
    if(weather_monitoring_active.load()) {
        std::cout << "Weather monitoring is already running." << std::endl;
        return;
    }
    
    weather_monitoring_active.store(true);
    
    // 初始化随机数种子
    srand(static_cast<unsigned int>(time(nullptr)));
    
    // 启动天气监测线程
    weather_thread = std::thread(weatherMonitoringLoop, initial_temperature, initial_humidity);
    
    std::cout << "Weather monitoring started. Will send data every 2 minutes." << std::endl;
}

void stopWeatherMonitoring() {
    if(!weather_monitoring_active.load()) {
        std::cout << "Weather monitoring is not running." << std::endl;
        return;
    }
    
    weather_monitoring_active.store(false);
    
    // 等待线程结束
    if(weather_thread.joinable()) {
        weather_thread.join();
    }
    
    std::cout << "Weather monitoring stopped." << std::endl;
}
