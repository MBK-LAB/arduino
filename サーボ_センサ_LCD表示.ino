//ライブラリのインクルード
//LCD(液晶モジュール),VL6180X(センサ),I2C通信,サーボの４つライブラリを利用
#include <LiquidCrystal_I2C.h>
#include <VL6180X.h>
#include <Wire.h>
#include <Servo.h>

//各ライブラリの変数宣言
VL6180X sensor;
LiquidCrystal_I2C lcd(0x27,20,4);

Servo myservo2;
Servo myservo3;
Servo myservo4;

//使用するint型変数の宣言
int pos = 0;
int sensor_data = 255;
int threshold = 25;

//setup()ではサーボ割当ピン宣言と初期位置移動、センサの初期設定、LCDの初期設定を行う
void setup() 
{
  Wire.begin();           //I2C通信開始

  pinMode(2, OUTPUT);    //デジタルピン２を出力ピンにする

  myservo2.attach(3);    //サーボとピンの組み合わせの宣言 サーボ２，３，４をデジタルピン３，５，６に割り当てる
  myservo3.attach(5);
  myservo4.attach(6);

  myservo2.write(45);    //各サーボを初期位置に移動させる
  myservo3.write(125);
  myservo4.write(90);

  //センサの初期設定
  sensor.init();      //センサー初期化
  sensor.configureDefault();      //デフォルト設定の構成
  sensor.writeReg(VL6180X::SYSRANGE__MAX_CONVERGENCE_TIME, 30);     //8bitレジスタに書き込み
  sensor.writeReg16Bit(VL6180X::SYSALS__INTEGRATION_PERIOD, 50);    //16bitレジスタに書き込み　細かい設定の詳細は不明　なくても動くことは確認済み
  sensor.setTimeout(500);   //タイムアウトの秒数設定(500ms)
  delay(300);
  sensor.startInterleavedContinuous(100);   //連続インターリーブ測定開始

  //LCDの初期設定
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Start robot_arm");
  delay(500);
  lcd.clear();

}

void loop() 
{
  for(pos=125; pos>50; pos-=1)
  {
    myservo3.write(pos);
    delay(15);
  }

  while(sensor_data > threshold)
  {
    sensor_data = sensor.readRangeContinuousMillimeters();
    lcd.setCursor(0, 0);
    lcd.print("sensor_data:");
    lcd.setCursor(13, 0);
    lcd.print(sensor_data);

    if (sensor_data > threshold)
    {
      lcd.setCursor(0, 1);
      lcd.print("Not catch");
    }
    else
    {
      lcd.setCursor(0, 1);
      lcd.print("Go catch");
    }
    
    if(sensor.timeoutOccurred())
    {
      lcd.setCursor(0, 2);
      lcd.print("Error");
      lcd.setCursor(0,3);
      lcd.print("Time out");
    }  
  }

  for(pos=45; pos<70; pos+=1)
  {
   myservo2.write(70);
   delay(5);
  }
  digitalWrite(2, HIGH);
  lcd.setCursor(0, 2);
  lcd.print("Air chuck close");
  delay(500);
  
  for(pos=70; pos>45; pos-=1)
  {
   myservo2.write(45);
   delay(15);
  }
  sensor_data = 255;
  delay(100);




  for(pos=50; pos<125; pos+=1)
  {
    myservo3.write(pos);
    delay(15);
  }

  for(pos=90; pos>0; pos-=1)
  { 
    myservo4.write(pos);
    delay(15);
  }
  delay(1000);

  digitalWrite(2, LOW);
  lcd.setCursor(0, 2);
  lcd.print("Air chuck open");

  for(pos=0; pos<90; pos+=1)
  {
    myservo4.write(pos);
    delay(15);
  }
  delay(100);
  

  


}
