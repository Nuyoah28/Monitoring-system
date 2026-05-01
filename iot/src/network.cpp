#include "network.h"

#include <cstdlib>
#include <cstring>
#include <ctime>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>
#endif

namespace {

std::string getEnvOrDefault(const char* key, const std::string& fallback) {
    const char* value = std::getenv(key);
    return (value && *value) ? std::string(value) : fallback;
}

int getEnvOrDefaultInt(const char* key, int fallback) {
    const char* value = std::getenv(key);
    return (value && *value) ? std::atoi(value) : fallback;
}

std::string getTimestamp() {
    std::time_t now = std::time(nullptr);
    std::tm tm_buf;
#ifdef _WIN32
    localtime_s(&tm_buf, &now);
#else
    localtime_r(&now, &tm_buf);
#endif
    char buffer[32];
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &tm_buf);
    return std::string(buffer);
}

std::string makeClipId() {
    std::ostringstream oss;
    oss << getEnvOrDefault("MQTT_ALARM_CLIP_PREFIX", "mqtt-alarm") << '-' << std::time(nullptr);
    return oss.str();
}

void appendUtf8String(std::vector<unsigned char>& buffer, const std::string& value) {
    const unsigned short len = static_cast<unsigned short>(value.size());
    buffer.push_back(static_cast<unsigned char>((len >> 8) & 0xFF));
    buffer.push_back(static_cast<unsigned char>(len & 0xFF));
    buffer.insert(buffer.end(), value.begin(), value.end());
}

void appendRemainingLength(std::vector<unsigned char>& buffer, std::size_t value) {
    do {
        unsigned char encoded = static_cast<unsigned char>(value % 128);
        value /= 128;
        if (value > 0) {
            encoded |= 0x80;
        }
        buffer.push_back(encoded);
    } while (value > 0);
}

class SocketHandle {
public:
#ifdef _WIN32
    using NativeSocket = SOCKET;
    static constexpr NativeSocket kInvalid = INVALID_SOCKET;
#else
    using NativeSocket = int;
    static constexpr NativeSocket kInvalid = -1;
#endif

    SocketHandle() : socket_(kInvalid) {}
    ~SocketHandle() { close(); }

    void reset(NativeSocket socket) {
        close();
        socket_ = socket;
    }

    NativeSocket get() const { return socket_; }
    bool valid() const { return socket_ != kInvalid; }

    void close() {
        if (!valid()) {
            return;
        }
#ifdef _WIN32
        closesocket(socket_);
#else
        ::close(socket_);
#endif
        socket_ = kInvalid;
    }

private:
    NativeSocket socket_;
};

#ifdef _WIN32
class WinsockGuard {
public:
    WinsockGuard() : active_(false) {
        WSADATA wsa_data;
        active_ = (WSAStartup(MAKEWORD(2, 2), &wsa_data) == 0);
    }

    ~WinsockGuard() {
        if (active_) {
            WSACleanup();
        }
    }

    bool active() const { return active_; }

private:
    bool active_;
};
#endif

bool sendAll(SocketHandle::NativeSocket socket_fd, const std::vector<unsigned char>& buffer) {
    std::size_t sent = 0;
    while (sent < buffer.size()) {
#ifdef _WIN32
        int result = send(socket_fd,
                          reinterpret_cast<const char*>(buffer.data() + sent),
                          static_cast<int>(buffer.size() - sent), 0);
#else
        ssize_t result = send(socket_fd, buffer.data() + sent, buffer.size() - sent, 0);
#endif
        if (result <= 0) {
            return false;
        }
        sent += static_cast<std::size_t>(result);
    }
    return true;
}

bool recvAll(SocketHandle::NativeSocket socket_fd, unsigned char* buffer, std::size_t size) {
    std::size_t received = 0;
    while (received < size) {
#ifdef _WIN32
        int result = recv(socket_fd, reinterpret_cast<char*>(buffer + received),
                          static_cast<int>(size - received), 0);
#else
        ssize_t result = recv(socket_fd, buffer + received, size - received, 0);
#endif
        if (result <= 0) {
            return false;
        }
        received += static_cast<std::size_t>(result);
    }
    return true;
}

bool connectTcp(SocketHandle& socket_handle, const std::string& host, int port) {
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    addrinfo* results = nullptr;
    std::string port_str = std::to_string(port);
    if (getaddrinfo(host.c_str(), port_str.c_str(), &hints, &results) != 0) {
        return false;
    }

    bool connected = false;
    for (addrinfo* rp = results; rp != nullptr; rp = rp->ai_next) {
        SocketHandle::NativeSocket socket_fd = ::socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (socket_fd == SocketHandle::kInvalid) {
            continue;
        }
        socket_handle.reset(socket_fd);
        if (::connect(socket_fd, rp->ai_addr, static_cast<int>(rp->ai_addrlen)) == 0) {
            connected = true;
            break;
        }
        socket_handle.close();
    }

    freeaddrinfo(results);
    return connected;
}

std::vector<unsigned char> buildConnectPacket(
        const std::string& client_id,
        const std::string& username,
        const std::string& password) {
    std::vector<unsigned char> variable_header;
    appendUtf8String(variable_header, "MQTT");
    variable_header.push_back(0x04);

    unsigned char connect_flags = 0x02;
    if (!username.empty()) {
        connect_flags |= 0x80;
    }
    if (!password.empty()) {
        connect_flags |= 0x40;
    }
    variable_header.push_back(connect_flags);
    variable_header.push_back(0x00);
    variable_header.push_back(0x3C);

    std::vector<unsigned char> payload;
    appendUtf8String(payload, client_id);
    if (!username.empty()) {
        appendUtf8String(payload, username);
    }
    if (!password.empty()) {
        appendUtf8String(payload, password);
    }

    std::vector<unsigned char> packet;
    packet.push_back(0x10);
    appendRemainingLength(packet, variable_header.size() + payload.size());
    packet.insert(packet.end(), variable_header.begin(), variable_header.end());
    packet.insert(packet.end(), payload.begin(), payload.end());
    return packet;
}

std::vector<unsigned char> buildPublishPacket(const std::string& topic, const std::string& payload) {
    std::vector<unsigned char> variable_header;
    appendUtf8String(variable_header, topic);

    std::vector<unsigned char> packet;
    packet.push_back(0x30);
    appendRemainingLength(packet, variable_header.size() + payload.size());
    packet.insert(packet.end(), variable_header.begin(), variable_header.end());
    packet.insert(packet.end(), payload.begin(), payload.end());
    return packet;
}

std::vector<unsigned char> buildDisconnectPacket() {
    return {0xE0, 0x00};
}

bool publishMqttMessage(const std::string& topic, const std::string& payload) {
    const std::string host = getEnvOrDefault("MQTT_BROKER_HOST", "127.0.0.1");
    const int port = getEnvOrDefaultInt("MQTT_BROKER_PORT", 1883);
    const std::string username = getEnvOrDefault("MQTT_USERNAME", "");
    const std::string password = getEnvOrDefault("MQTT_PASSWORD", "");
    const std::string client_id = getEnvOrDefault("MQTT_CLIENT_ID", "iot-algo-publisher");

#ifdef _WIN32
    WinsockGuard winsock_guard;
    if (!winsock_guard.active()) {
        return false;
    }
#endif

    SocketHandle socket_handle;
    if (!connectTcp(socket_handle, host, port)) {
        std::cerr << "MQTT TCP connect failed: " << host << ':' << port << std::endl;
        return false;
    }

    if (!sendAll(socket_handle.get(), buildConnectPacket(client_id, username, password))) {
        std::cerr << "MQTT CONNECT send failed" << std::endl;
        return false;
    }

    unsigned char connack[4];
    if (!recvAll(socket_handle.get(), connack, sizeof(connack))) {
        std::cerr << "MQTT CONNACK receive failed" << std::endl;
        return false;
    }
    if (connack[0] != 0x20 || connack[1] != 0x02 || connack[3] != 0x00) {
        std::cerr << "MQTT CONNACK rejected, code=" << static_cast<int>(connack[3]) << std::endl;
        return false;
    }

    if (!sendAll(socket_handle.get(), buildPublishPacket(topic, payload))) {
        std::cerr << "MQTT PUBLISH send failed" << std::endl;
        return false;
    }

    sendAll(socket_handle.get(), buildDisconnectPacket());
    return true;
}

}  // namespace

void triggerAlarm() {
    const std::string device_code = getEnvOrDefault("DEVICE_CODE", "iot-algo-01");
    const std::string topic = getEnvOrDefault(
            "MQTT_TOPIC_ALARM",
            "iot/algo/" + device_code + "/alarm");
    const int camera_id = getEnvOrDefaultInt("ALARM_CAMERA_ID", 1);
    const int case_type = getEnvOrDefaultInt("ALARM_CASE_TYPE", 1);
    const std::string clip_id = makeClipId();
    const std::string occurred_at = getTimestamp();

    std::ostringstream payload;
    payload << "{\"cameraId\":" << camera_id
            << ",\"caseType\":" << case_type
            << ",\"clipId\":\"" << clip_id
            << "\",\"occurredAt\":\"" << occurred_at
            << "\"}";

    if (!publishMqttMessage(topic, payload.str())) {
        std::cerr << "triggerAlarm mqtt publish failed" << std::endl;
    } else {
        std::cout << "Alarm published to MQTT topic: " << topic << std::endl;
    }
}
