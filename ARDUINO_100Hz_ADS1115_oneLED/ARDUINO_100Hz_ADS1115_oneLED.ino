#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

const unsigned long BAUD = 115200;

const int RED_LED = 3;
const int IR_LED  = 2;

const uint8_t TIA_CHANNEL = 0;

const uint32_t LED_PERIOD  = 5000;  // us
const uint32_t SETTLE_TIME = 2500;  // us
// 150k ohms + 2200 pF --> 5*RC = 1.65ms
// 860 samples/sec = 1.16ms per sample 

uint32_t start_time = 0;

bool recording = false;

struct Sample
{
    uint32_t time_red_us;
    int16_t tia_red;

    uint32_t time_ir_us;
    int16_t tia_ir;
};

Sample s;

const uint8_t START_PACKET = 0xFA;
const uint8_t DATA_PACKET  = 0xAA;
const uint8_t END_PACKET   = 0xFB;

const char START_CMD = 's';
const char STOP_CMD  = 'q';


void setup()
{
    Serial.begin(BAUD);

    Wire.begin();

    if (!ads.begin())
    {
        while (1);
    }

    ads.setGain(GAIN_ONE);
    ads.setDataRate(RATE_ADS1115_860SPS);

    pinMode(RED_LED, OUTPUT);
    pinMode(IR_LED, OUTPUT);

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, LOW);

    static_assert(
        sizeof(Sample) == 12,
        "Sample struct must be 12 bytes"
    );
}


void loop()
{
    // ========================================================
    // SERIAL
    // ========================================================

    while (Serial.available() > 0)
    {
        char cmd = Serial.read();

        if (cmd == START_CMD)
        {
            recording = true;

            digitalWrite(RED_LED, LOW);
            digitalWrite(IR_LED, LOW);

            delay(1000);

            start_time = micros();

            Serial.write(START_PACKET);
        }

        else if (cmd == STOP_CMD)
        {
            recording = false;

            digitalWrite(RED_LED, LOW);
            digitalWrite(IR_LED, LOW);

            Serial.write(END_PACKET);
        }
    }


    if (!recording)
        return;


    // ========================================================
    // RED
    // ========================================================

    uint32_t t0 = micros();

    digitalWrite(IR_LED, LOW);
    digitalWrite(RED_LED, HIGH);

    // Wait for TIA settling
    while ((uint32_t)(micros() - t0) < SETTLE_TIME);

    // Timestamp ADC conversion start
    s.time_red_us = micros() - start_time;
    // BLOCKING ADS1115 conversion (blocks for 1.16ms)
    s.tia_red = ads.readADC_SingleEnded(TIA_CHANNEL);

    // Keep RED on for full 5 ms
    while ((uint32_t)(micros() - t0) < LED_PERIOD);

    digitalWrite(RED_LED, LOW);

    // ========================================================
    // IR
    // ========================================================

    t0 = micros();

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, HIGH);

    // Wait for TIA settling
    while ((uint32_t)(micros() - t0) < SETTLE_TIME);

    // Timestamp ADC conversion start
    s.time_ir_us = micros() - start_time;
    // BLOCKING ADS1115 conversion
    s.tia_ir = ads.readADC_SingleEnded(TIA_CHANNEL);

    // Keep IR on for full 5 ms
    while ((uint32_t)(micros() - t0) < LED_PERIOD);

    digitalWrite(IR_LED, LOW);

    // ========================================================
    // SEND
    // ========================================================

    Serial.write(DATA_PACKET);

    Serial.write((uint8_t*)&s, sizeof(s));
}