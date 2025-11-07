/*
  Ultrasonic distance sender for HC-SR04 on Mega2560
  Sends "DIST:<cm>" every 500ms over Serial
*/

#define TRIG_PIN 8
#define ECHO_PIN 9

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.println("Distance sensor ready");
}

void loop() {
  // Send a 10 µs pulse to trigger
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure echo duration
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30 ms timeout (~5 m)
  float distance_cm = duration * 0.0343 / 2.0;

  if (duration == 0) {
    Serial.println("DIST:OutOfRange");
  } else {
    Serial.print("DIST:");
    Serial.println(distance_cm, 1);
  }

  delay(500);
}