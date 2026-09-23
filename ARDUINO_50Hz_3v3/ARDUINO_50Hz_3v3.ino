const unsigned long BAUD = 115200; 

// ---------- Pin definitions ----------
const int RED_LED = 3; // yellow
const int IR_LED  = 2; // green

const int TIA_PIN = A3;

uint32_t start_time = 0;

// ---------- Timing ----------
// 200Hz
const unsigned long LED_PERIOD = 5000;    // 10ms+10ms = 20ms -> 1/20ms = 50Hz // 25Hz
const unsigned long SETTLE_TIME = 2000;    // 8 ms
// 220k ohm, 4700pF, 5 tau = 5.17ms (this one 10/08/2026 2.36pm)

int16_t dark = 0;
unsigned long t0 = 0;

bool recording = false;

struct Sample
{
    uint32_t time_red_us; // 4 bytes
    int16_t tia_red; // 2 byte
    uint32_t time_ir_us; // 4 bytes
    int16_t tia_ir; // 2 byte
};

Sample s;

// all 1 byte
const uint8_t START_PACKET = 0xFA;
const uint8_t DATA_PACKET  = 0xAA;
const uint8_t END_PACKET   = 0xFB;

const char START_CMD = 's';
const char STOP_CMD  = 'q';


void setup()
{
    Serial.begin(BAUD);
    delay(1000);

    // need to connect AREF to 3.3V
    analogReference(EXTERNAL);
    
    pinMode(RED_LED, OUTPUT);
    pinMode(IR_LED, OUTPUT);

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, LOW);

    static_assert(sizeof(Sample) == 12, "Sample struct must be 12 bytes");

}

void loop()
{
    // ---------- Handle serial commands ----------
    while (Serial.available() > 0)
    {
        char cmd = Serial.read();

        if (cmd == START_CMD)
        {
            recording = true;

            digitalWrite(RED_LED, LOW);
            digitalWrite(IR_LED, LOW);
            delay(1000);

            dark = analogRead(TIA_PIN);

            start_time = micros(); // Reset timestamps
            Serial.write(START_PACKET);
        }
        else if (cmd == STOP_CMD)
        {
            recording = false;

            Serial.write(END_PACKET);   // Acknowledge stop

            digitalWrite(RED_LED, LOW);
            digitalWrite(IR_LED, LOW);
            delay(1000);
        }
    }
    if (!recording)
    {
        return;
    }

    int16_t tia_red;
    int16_t tia_ir;

    //================ RED =================//
    
    t0 = micros();
    
    digitalWrite(IR_LED, LOW);
    digitalWrite(RED_LED, HIGH);

    while (micros() - t0 < SETTLE_TIME);

    unsigned long timestamp_red = micros() - start_time;
    
    tia_red = analogRead(TIA_PIN);
    // tia_red = analogRead(TIA_PIN) - dark;

    while (micros() - t0 < LED_PERIOD);
    
    digitalWrite(RED_LED, LOW);

    //================ IR =================//

    t0 = micros();

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, HIGH);

    while (micros() - t0 < SETTLE_TIME);

    unsigned long timestamp_ir = micros() - start_time;

    tia_ir = analogRead(TIA_PIN);
    // tia_ir = analogRead(TIA_PIN) - dark;

    while (micros() - t0 < LED_PERIOD);

    digitalWrite(IR_LED, LOW);

    //================ SEND =================//
    s.time_red_us = timestamp_red;
    s.tia_red = tia_red;
    s.time_ir_us = timestamp_ir;
    s.tia_ir = tia_ir;    
    
    Serial.write(DATA_PACKET);
    Serial.write((uint8_t*)&s, sizeof(s));
    
}
