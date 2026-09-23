#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

const unsigned long BAUD = 115200;

const int MODE = 0; // 0 = red, 1 = ir

const int RED_LED = 3;
const int IR_LED  = 2;

const uint8_t TIA_CHANNEL = 0;

const uint32_t SAMPLE_PERIOD_US = 5000;   // 1/5ms = 200 Hz
uint32_t start_time = 0;
uint32_t next_sample_time = 0;

bool recording = false;

struct Sample {
    uint32_t time_red_us;
    int16_t tia_red;

    uint32_t time_ir_us;
    int16_t tia_ir;
};

Sample s;

uint32_t timestamp;
int16_t adc_value;

const uint8_t START_PACKET = 0xFA;
const uint8_t DATA_PACKET  = 0xAA;
const uint8_t END_PACKET   = 0xFB;

const char START_CMD = 's';
const char STOP_CMD  = 'q';


void setup() {
    Serial.begin(BAUD);

    Wire.begin();

    if (!ads.begin()) {
        while (1);
    }

    // +/- 4.096 V
    ads.setGain(GAIN_ONE);

    // ADS1115 conversion rate
    ads.setDataRate(RATE_ADS1115_860SPS);

    pinMode(RED_LED, OUTPUT);
    pinMode(IR_LED, OUTPUT);

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, LOW);

    static_assert(sizeof(Sample) == 12, "Sample struct must be 12 bytes");
}

void loop()
{
    while (Serial.available() > 0) {
        char cmd = Serial.read();

        if (cmd == START_CMD) {
            recording = true;

            // Continuous RED illumination
            if (MODE == 0) {
                digitalWrite(IR_LED, LOW);
                digitalWrite(RED_LED, HIGH);
            } else {
                digitalWrite(IR_LED, HIGH);
                digitalWrite(RED_LED, LOW);
            }

            // Plenty of time for TIA to settle
            delay(1000);

            start_time = micros();

            // First sample immediately
            next_sample_time = start_time;

            Serial.write(START_PACKET);
        }

        else if (cmd == STOP_CMD) {
            recording = false;

            digitalWrite(RED_LED, LOW);
            digitalWrite(IR_LED, LOW);

            Serial.write(END_PACKET);
        }
    }


    if (!recording) {
        return;
    }

    // 200 Hz SAMPLING (1 LED ONLY)
    uint32_t now = micros();


    // Signed comparison handles micros() rollover correctly
    if ((int32_t)(now - next_sample_time) >= 0) {
        // ADS1115 blocking single-shot conversion ~1.16 ms at 860 SPS
        timestamp = micros() - start_time;
        adc_value = ads.readADC_SingleEnded(TIA_CHANNEL);

        s.time_red_us = timestamp;
        s.time_ir_us = timestamp;

        if (MODE == 0) {
            s.tia_red = adc_value; 
            s.tia_ir = 0;    
        } else {
            s.tia_ir = adc_value;
            s.tia_red = 0;
        }
        Serial.write(DATA_PACKET);

        Serial.write((uint8_t*)&s, sizeof(s));

        next_sample_time += SAMPLE_PERIOD_US;
    }
}