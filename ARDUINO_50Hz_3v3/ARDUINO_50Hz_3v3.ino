const unsigned long BAUD = 500000; 

// ---------- Pin definitions ----------
const int RED_LED = 5; // yellow
const int IR_LED  = 6; // green

const int TIA_PIN = A0;

uint32_t start_time = 0;

// ---------- Timing ----------
const unsigned long LED_PERIOD = 10000;    // 10ms+10ms = 20ms -> 1/20ms = 50Hz
const unsigned long SETTLE_TIME = 5000;    // 5 ms
// To bring ANALOG READ down to 3.3V: Rf = 150k ohms, Cf = 4700p -> 225Hz, 5*tau = 705us*5= 3.525ms

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

    // need to connect AREF to 3.3V
    analogReference(EXTERNAL);

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
            delayMicroseconds(LED_PERIOD);

            dark = analogRead(TIA_PIN);

            start_time = micros(); // Reset timestamps
            Serial.write(START_PACKET);

            return;
        }
        else if (cmd == STOP_CMD)
        {
            recording = false;

            Serial.write(END_PACKET);   // Acknowledge stop

            return;
        }
    

        if (!recording)
        {
            return;
        }
    }

    int16_t tia_red;
    int16_t tia_ir;

    //================ RED =================//
    
    t0 = micros();
    
    digitalWrite(IR_LED, LOW);
    digitalWrite(RED_LED, HIGH);

    while (micros() - t0 < SETTLE_TIME);

    unsigned long timestamp_red = micros() - start_time;
    
    tia_red = analogRead(TIA_PIN) - dark;

    while (micros() - t0 < LED_PERIOD);

    //================ IR =================//

    t0 = micros();

    digitalWrite(RED_LED, LOW);
    digitalWrite(IR_LED, HIGH);

    while (micros() - t0 < SETTLE_TIME);

    unsigned long timestamp_ir = micros() - start_time;

    tia_ir = analogRead(TIA_PIN) - dark;

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
