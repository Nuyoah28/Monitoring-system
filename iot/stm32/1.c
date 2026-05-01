#include "stm32f10x.h"
#include "stm32f10x_adc.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_rcc.h"
#include "stm32f10x_usart.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

/* SHT30 on I2C1: PB6=SCL, PB7=SDA, ADDR tied to GND => 0x44 */
#define SHT30_SCL_PIN     GPIO_Pin_6
#define SHT30_SDA_PIN     GPIO_Pin_7
#define SHT30_I2C_PORT    GPIOB
#define SHT30_ADDR        0x44

/* GP2Y + MQ9 + USART */
#define GP2Y_LED_PIN      GPIO_Pin_0
#define GP2Y_AO_PIN       GPIO_Pin_1
#define MQ9_AO_PIN        GPIO_Pin_3
#define UART_TX_PIN       GPIO_Pin_9
#define UART_RX_PIN       GPIO_Pin_10
#define BOARD_LED_PIN     GPIO_Pin_13

#define GP2Y_LED_PORT     GPIOA
#define UART_PORT         GPIOA
#define BOARD_LED_PORT    GPIOC

#define TX_BUF_LEN        128
#define VREF              3.3f
#define ADC_FULL_SCALE    4096.0f
#define SHT30_WRITE_ADDR  ((uint8_t)(SHT30_ADDR << 1))
#define SHT30_READ_ADDR   ((uint8_t)((SHT30_ADDR << 1) | 0x01))

static uint8_t TxBuf[TX_BUF_LEN];

void LED_Init(void);
void LED_On(void);
void LED_Off(void);
void LED_Toggle(void);
void Delay_ms(uint32_t ms);
void Delay_Short(volatile uint32_t cycles);

void ADC_Init_All(void);
u16 Get_ADC_Value(u8 channel);
u16 Get_ADC_Average(u8 channel, u8 times);
u16 Read_GP2Y1014AU(void);
u16 Read_MQ9(void);

void USART1_Init(void);
void MyPrintf(const char *__format, ...);

void I2C1_Init_SHT30(void);
void SHT30_SDA_Out(void);
void SHT30_SDA_In(void);
void SHT30_I2C_Delay(void);
void SHT30_I2C_Start(void);
void SHT30_I2C_Stop(void);
uint8_t SHT30_I2C_WaitAck(void);
void SHT30_I2C_SendAck(uint8_t ack);
void SHT30_I2C_WriteByte(uint8_t byte);
uint8_t SHT30_I2C_ReadByte(uint8_t ack);
uint8_t SHT30_CRC8(uint8_t *data, uint8_t len);
uint8_t SHT30_WriteCmd(uint16_t cmd);
uint8_t SHT30_ReadBytes(uint8_t *buf, uint8_t len);
uint8_t SHT30_ReadTempHumidity(float *temp, float *humi);

uint8_t IOT_XorChecksum(const char *body);
void Send_IOT_ENV_Frame(float temperature, float humidity);
float Convert_ADC_To_Voltage(u16 adc_value);
float Convert_GP2Y_To_DustDensity(float voltage);

void LED_Init(void) {
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);

    GPIO_InitStructure.GPIO_Pin = BOARD_LED_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(BOARD_LED_PORT, &GPIO_InitStructure);

    GPIO_SetBits(BOARD_LED_PORT, BOARD_LED_PIN);
}

void LED_On(void) {
    GPIO_ResetBits(BOARD_LED_PORT, BOARD_LED_PIN);
}

void LED_Off(void) {
    GPIO_SetBits(BOARD_LED_PORT, BOARD_LED_PIN);
}

void LED_Toggle(void) {
    if (GPIO_ReadOutputDataBit(BOARD_LED_PORT, BOARD_LED_PIN) == Bit_SET) {
        LED_On();
    } else {
        LED_Off();
    }
}

void Delay_ms(uint32_t ms) {
    uint32_t i;
    uint32_t j;

    for (i = 0; i < ms; i++) {
        for (j = 0; j < 7200; j++) {
        }
    }
}

void Delay_Short(volatile uint32_t cycles) {
    while (cycles--) {
    }
}

void ADC_Init_All(void) {
    GPIO_InitTypeDef GPIO_InitStructure;
    ADC_InitTypeDef ADC_InitStruct;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_ADC1, ENABLE);

    GPIO_InitStructure.GPIO_Pin = GP2Y_LED_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GP2Y_LED_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = GP2Y_AO_PIN | MQ9_AO_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    RCC_ADCCLKConfig(RCC_PCLK2_Div6);
    ADC_DeInit(ADC1);

    ADC_InitStruct.ADC_Mode = ADC_Mode_Independent;
    ADC_InitStruct.ADC_ScanConvMode = DISABLE;
    ADC_InitStruct.ADC_ContinuousConvMode = DISABLE;
    ADC_InitStruct.ADC_ExternalTrigConv = ADC_ExternalTrigConv_None;
    ADC_InitStruct.ADC_DataAlign = ADC_DataAlign_Right;
    ADC_InitStruct.ADC_NbrOfChannel = 1;
    ADC_Init(ADC1, &ADC_InitStruct);

    ADC_Cmd(ADC1, ENABLE);

    ADC_ResetCalibration(ADC1);
    while (ADC_GetResetCalibrationStatus(ADC1)) {
    }

    ADC_StartCalibration(ADC1);
    while (ADC_GetCalibrationStatus(ADC1)) {
    }
}

u16 Get_ADC_Value(u8 channel) {
    ADC_RegularChannelConfig(ADC1, channel, 1, ADC_SampleTime_239Cycles5);
    ADC_SoftwareStartConvCmd(ADC1, ENABLE);

    while (!ADC_GetFlagStatus(ADC1, ADC_FLAG_EOC)) {
    }

    return ADC_GetConversionValue(ADC1);
}

u16 Get_ADC_Average(u8 channel, u8 times) {
    u32 temp_val = 0;
    u8 t;

    for (t = 0; t < times; t++) {
        temp_val += Get_ADC_Value(channel);
        Delay_ms(5);
    }
    return (u16)(temp_val / times);
}

u16 Read_GP2Y1014AU(void) {
    u16 adc_value;

    /* Keep the original board logic: high level turns the dust LED on. */
    GPIO_SetBits(GP2Y_LED_PORT, GP2Y_LED_PIN);
    Delay_Short(200);

    adc_value = Get_ADC_Value(1);

    Delay_Short(30);
    GPIO_ResetBits(GP2Y_LED_PORT, GP2Y_LED_PIN);
    Delay_ms(10);

    return adc_value;
}

u16 Read_MQ9(void) {
    return Get_ADC_Average(3, 10);
}

void USART1_Init(void) {
    GPIO_InitTypeDef GPIO_InitStructure;
    USART_InitTypeDef USART_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1 | RCC_APB2Periph_GPIOA, ENABLE);

    GPIO_InitStructure.GPIO_Pin = UART_TX_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(UART_PORT, &GPIO_InitStructure);

    GPIO_InitStructure.GPIO_Pin = UART_RX_PIN;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
    GPIO_Init(UART_PORT, &GPIO_InitStructure);

    USART_InitStructure.USART_BaudRate = 115200;
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;
    USART_InitStructure.USART_StopBits = USART_StopBits_1;
    USART_InitStructure.USART_Parity = USART_Parity_No;
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
    USART_Init(USART1, &USART_InitStructure);

    USART_Cmd(USART1, ENABLE);
}

void MyPrintf(const char *__format, ...)
{
    va_list ap;
    int len;
    int i;

    va_start(ap, __format);
    memset(TxBuf, 0, TX_BUF_LEN);
    vsnprintf((char*)TxBuf, TX_BUF_LEN, __format, ap);
    va_end(ap);

    len = strlen((const char*)TxBuf);
    for (i = 0; i < len; i++) {
        while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET) {
        }
        USART_SendData(USART1, TxBuf[i]);
    }
}

void I2C1_Init_SHT30(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);

    GPIO_InitStructure.GPIO_Pin = SHT30_SCL_PIN | SHT30_SDA_PIN;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD;
    GPIO_Init(SHT30_I2C_PORT, &GPIO_InitStructure);

    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN | SHT30_SDA_PIN);
}

void SHT30_SDA_Out(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = SHT30_SDA_PIN;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_OD;
    GPIO_Init(SHT30_I2C_PORT, &GPIO_InitStructure);
}

void SHT30_SDA_In(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;

    GPIO_InitStructure.GPIO_Pin = SHT30_SDA_PIN;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_Init(SHT30_I2C_PORT, &GPIO_InitStructure);
}

void SHT30_I2C_Delay(void)
{
    Delay_Short(40);
}

void SHT30_I2C_Start(void)
{
    SHT30_SDA_Out();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SDA_PIN | SHT30_SCL_PIN);
    SHT30_I2C_Delay();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    SHT30_I2C_Delay();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
}

void SHT30_I2C_Stop(void)
{
    SHT30_SDA_Out();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    SHT30_I2C_Delay();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    SHT30_I2C_Delay();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    SHT30_I2C_Delay();
}

uint8_t SHT30_I2C_WaitAck(void)
{
    uint16_t timeout = 0;

    SHT30_SDA_In();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    SHT30_I2C_Delay();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    SHT30_I2C_Delay();

    while (GPIO_ReadInputDataBit(SHT30_I2C_PORT, SHT30_SDA_PIN)) {
        timeout++;
        if (timeout > 250) {
            SHT30_I2C_Stop();
            return 0;
        }
    }

    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    return 1;
}

void SHT30_I2C_SendAck(uint8_t ack)
{
    SHT30_SDA_Out();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);

    if (ack) {
        GPIO_SetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    } else {
        GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
    }

    SHT30_I2C_Delay();
    GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    SHT30_I2C_Delay();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
}

void SHT30_I2C_WriteByte(uint8_t byte)
{
    uint8_t i;

    SHT30_SDA_Out();
    GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);

    for (i = 0; i < 8; i++) {
        if (byte & 0x80) {
            GPIO_SetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
        } else {
            GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SDA_PIN);
        }
        byte <<= 1;
        SHT30_I2C_Delay();
        GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
        SHT30_I2C_Delay();
        GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
    }
}

uint8_t SHT30_I2C_ReadByte(uint8_t ack)
{
    uint8_t i;
    uint8_t byte = 0;

    SHT30_SDA_In();
    for (i = 0; i < 8; i++) {
        byte <<= 1;
        GPIO_ResetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
        SHT30_I2C_Delay();
        GPIO_SetBits(SHT30_I2C_PORT, SHT30_SCL_PIN);
        if (GPIO_ReadInputDataBit(SHT30_I2C_PORT, SHT30_SDA_PIN)) {
            byte |= 0x01;
        }
        SHT30_I2C_Delay();
    }

    SHT30_I2C_SendAck(ack);
    return byte;
}

uint8_t SHT30_CRC8(uint8_t *data, uint8_t len)
{
    uint8_t crc = 0xFF;
    uint8_t i;
    uint8_t j;

    for (i = 0; i < len; i++) {
        crc ^= data[i];
        for (j = 0; j < 8; j++) {
            if (crc & 0x80) {
                crc = (uint8_t)((crc << 1) ^ 0x31);
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

uint8_t SHT30_WriteCmd(uint16_t cmd)
{
    SHT30_I2C_Start();
    SHT30_I2C_WriteByte(SHT30_WRITE_ADDR);
    if (!SHT30_I2C_WaitAck()) {
        return 0;
    }

    SHT30_I2C_WriteByte((uint8_t)((cmd >> 8) & 0xFF));
    if (!SHT30_I2C_WaitAck()) {
        return 0;
    }

    SHT30_I2C_WriteByte((uint8_t)(cmd & 0xFF));
    if (!SHT30_I2C_WaitAck()) {
        return 0;
    }

    SHT30_I2C_Stop();
    return 1;
}

uint8_t SHT30_ReadBytes(uint8_t *buf, uint8_t len)
{
    uint8_t i;

    SHT30_I2C_Start();
    SHT30_I2C_WriteByte(SHT30_READ_ADDR);
    if (!SHT30_I2C_WaitAck()) {
        return 0;
    }

    for (i = 0; i < len; i++) {
        buf[i] = SHT30_I2C_ReadByte((uint8_t)(i == len - 1));
    }

    SHT30_I2C_Stop();
    return 1;
}

uint8_t SHT30_ReadTempHumidity(float *temp, float *humi)
{
    uint8_t buf[6];
    uint16_t rawT;
    uint16_t rawH;

    if (!SHT30_WriteCmd(0x2400)) {
        return 0;
    }
    Delay_ms(20);

    if (!SHT30_ReadBytes(buf, 6)) {
        return 0;
    }

    if (SHT30_CRC8(buf, 2) != buf[2]) {
        return 0;
    }
    if (SHT30_CRC8(buf + 3, 2) != buf[5]) {
        return 0;
    }

    rawT = ((uint16_t)buf[0] << 8) | buf[1];
    rawH = ((uint16_t)buf[3] << 8) | buf[4];

    *temp = -45.0f + 175.0f * ((float)rawT / 65535.0f);
    *humi = 100.0f * ((float)rawH / 65535.0f);

    return 1;
}

uint8_t IOT_XorChecksum(const char *body)
{
    uint8_t cs = 0;

    while (*body) {
        cs ^= (uint8_t)(*body);
        body++;
    }
    return cs;
}

void Send_IOT_ENV_Frame(float temperature, float humidity)
{
    char body[64];
    uint8_t checksum;

    snprintf(body, sizeof(body), "IOT,1,ENV,%.1f,%.1f", temperature, humidity);
    checksum = IOT_XorChecksum(body);
    MyPrintf("$%s*%02X\r\n", body, checksum);
}

float Convert_ADC_To_Voltage(u16 adc_value)
{
    return ((float)adc_value * VREF) / ADC_FULL_SCALE;
}

float Convert_GP2Y_To_DustDensity(float voltage)
{
    if (voltage > 0.5f) {
        return (voltage - 0.5f) * 0.17f;
    }
    return 0.0f;
}

int main(void) {
    u16 gp2y_value;
    u16 mq9_value;
    float gp2y_voltage;
    float mq9_voltage;
    float dust_density;
    float sht30_temp = 0.0f;
    float sht30_humi = 0.0f;
    uint8_t blink_counter = 0;
    int i;

    SystemInit();

    LED_Init();
    ADC_Init_All();
    USART1_Init();
    I2C1_Init_SHT30();

    MyPrintf("\r\nSensor collector starting...\r\n");
    MyPrintf("SHT30 + GP2Y1014AU + MQ9\r\n");
    MyPrintf("---------------------------\r\n");

    for (i = 0; i < 6; i++) {
        LED_Toggle();
        Delay_ms(200);
    }
    LED_Off();

    while (1) {
        LED_On();

        gp2y_value = Read_GP2Y1014AU();
        mq9_value = Read_MQ9();
        gp2y_voltage = Convert_ADC_To_Voltage(gp2y_value);
        mq9_voltage = Convert_ADC_To_Voltage(mq9_value);
        dust_density = Convert_GP2Y_To_DustDensity(gp2y_voltage);

        LED_Off();

        if (SHT30_ReadTempHumidity(&sht30_temp, &sht30_humi)) {
            MyPrintf("SHT30 TEMP: %.2fC | HUM: %.2f%%\r\n", sht30_temp, sht30_humi);
            Send_IOT_ENV_Frame(sht30_temp, sht30_humi);
        } else {
            MyPrintf("SHT30 read failed\r\n");
        }

        MyPrintf("GP2Y ADC: %4d | Voltage: %.3fV | Dust: %.3fmg/m3\r\n",
                 gp2y_value, gp2y_voltage, dust_density);
        MyPrintf("MQ9  ADC: %4d | Voltage: %.3fV\r\n",
                 mq9_value, mq9_voltage);
        MyPrintf("---------------------------\r\n");

        blink_counter++;
        if (blink_counter >= 4) {
            LED_Toggle();
            Delay_ms(100);
            LED_Toggle();
            blink_counter = 0;
        }

        Delay_ms(2000);
    }
}

void USART1_IRQHandler(void) {
}
