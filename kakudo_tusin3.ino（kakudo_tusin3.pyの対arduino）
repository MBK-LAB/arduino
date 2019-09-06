// Arduino を Raspberry Pi で制御
#include <Servo.h>

//サーボの宣言
Servo handservo;    //グリッパーのサーボ
Servo myservo1;     //グリッパー取り付け部のサーボ
Servo myservo2;     //アーム上軸
Servo myservo3;     //アーム下軸
Servo myservo4;     //


//変数の宣言
int pos; //サーボ動作用の変数
int hand_servo, servo1, servo2, servo3, servo4; //サーボ角度読み込み用変数
int myspeed;  //サーボリセット時の移動速度変数


String data;
int data1;
int data2;
int data_len;
int old_data1 = 90;
int old_data2 = 90;
int x_move1, x_move2;
int y_move1, y_move2;
char dataT[50];

void setup() {
  handservo.attach(3);
  myservo1.attach(5);
  myservo2.attach(6);
  myservo3.attach(9);
  myservo4.attach(11);

  
    //handservo.write(10);
    //myservo1.write(90);
    myservo2.write(60);
    myservo3.write(120);
    myservo4.write(90);
  

  Serial.begin(57600);
}


void loop()
{
  //Serial.begin(57600);
  //myservo3.write(120);
  if (Serial.available() > 0)
  {
    data = Serial.readStringUntil("\n");
    //Serial.print(data);
    
    data_len = data.length();
    data.toCharArray(dataT, data_len);
    data1 = atoi(strtok(dataT, ","));
    data2 = atoi(strtok(NULL, ","));

    //Serial.println(data1);

    //myservo4.write(data1);
    delay(50);
    //myservo3.write(data2);
    Serial.println("end");
   }
    




}
