/*
  LLM_Controller.ino
  Elegoo Mega 2560 R3
  Basic serial command receiver for local LLM / Python bridge
*/

#include <DHT.h>
#include <DHT_U.h>


#define LED_PIN 2
#define MOTOR_PIN 7
#define TRIG_PIN 8
#define ECHO_PIN 9

#define DHTPIN 6
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);        // USB serial
  pinMode(LED_PIN, OUTPUT);       // onboard LED
  pinMode(MOTOR_PIN, OUTPUT);       // motor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  dht.begin();
  
  Serial.println("Arduino ready");
}

unsigned long lastPing = 0;
unsigned long lastDHT = 0;

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    Action(cmd);

  }

  // Distance every 500 ms
  if (millis() - lastPing > 500) {
    lastPing = millis();

    // Send a 10µs HIGH pulse to start the measurement
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    long duration = pulseIn(ECHO_PIN, HIGH, 30000); // timeout 30ms
    float distance = duration * 0.0343 / 2.0;
    Serial.print("DIST:");
    Serial.println(distance, 1);
  }

  // DHT every 2 s
  if (millis() - lastDHT > 2000) {
    lastDHT = millis();
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      Serial.print("TEMP:");
      Serial.print(t, 1);
      Serial.print(",HUM:");
      Serial.println(h, 1);
    } else {
      Serial.println("TEMP:ERROR");
    }
  }

}

void Action(String action) {
  action.toUpperCase();

    if (action.indexOf("LED_ON") >= 0) {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED turned ON");
    } else if (action.indexOf("LED_OFF") >= 0) {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED turned OFF");
    } else if (action.indexOf("TOGGLE_LED") >= 0) {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED toggled");
    } else if (action.indexOf("MOTOR_ON") >= 0) {
      digitalWrite(MOTOR_PIN, HIGH);
      Serial.println("MOTOR turned ON");
    } else if (action.indexOf("MOTOR_OFF") >= 0) {
      digitalWrite(MOTOR_PIN, LOW);
      Serial.println("MOTOR turned OFF");
    } else {
      Serial.print("Unknown command: ");
      Serial.println(action);
    }
}