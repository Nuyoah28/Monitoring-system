#ifndef NETWORK_H
#define NETWORK_H

void triggerAlarm();
void sendWeatherData(int temperature, int humidity);
void startWeatherMonitoring(int initial_temperature, int initial_humidity);
void stopWeatherMonitoring();

#endif // NETWORK_H