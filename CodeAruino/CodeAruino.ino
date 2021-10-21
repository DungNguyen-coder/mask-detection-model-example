#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Servo.h>

#define LED_BLUE 3
#define LED_RED 4
//#define DOOR     5
#define MLX90614_SDA A4
#define MLX90614_SCL A5
#define SERVO_PIN 9

Servo myServo;
bool doorIsOpen = 0;
int checkTimeOpenDoor = millis();

// khởi tạo object cho MLX90614
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

void setup()
{
  Serial.begin(9600);
  //  pinMode(DOOR, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);

  //  digitalWrite(DOOR, 0);
  digitalWrite(LED_RED, 1);
  digitalWrite(LED_BLUE, 0);

  myServo.attach(SERVO_PIN);
}

void openDoor()
{
  doorIsOpen = 1;
  checkTimeOpenDoor = millis();
  //  digitalWrite(DOOR, 1);
  digitalWrite(LED_RED, 0);
  digitalWrite(LED_BLUE, 1);
  myServo.write(90);
}

void closeDoor()
{
  doorIsOpen = 0;
  //  digitalWrite(DOOR, 0);
  digitalWrite(LED_RED, 1);
  digitalWrite(LED_BLUE, 0);
  myServo.write(0);
}
int redMlx90614()
{
  int tem_object = mlx.readObjectTempC();
  return tem_object;
}

void loop()
{
  if (Serial.available())
  {
    int tem_object = redMlx90614() * 100;
    while (Serial.available())
      Serial.read();
    // int tem_object = 3750;
    Serial.println(tem_object);
    openDoor();
  }

  if (doorIsOpen && millis() - checkTimeOpenDoor > 10000)
    closeDoor();
}
