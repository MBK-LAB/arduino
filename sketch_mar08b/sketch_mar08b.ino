
//ライブラリのインクルード
//LCD(液晶モジュール),VL6180X(センサ),I2C通信,サーボの４つライブラリを利用

#include <LiquidCrystal_I2C.h>
#include <VL6180X.h>
#include <Wire.h>
#include <Servo.h>

//各ライブラリの変数宣言
VL6180X sensor;
LiquidCrystal_I2C lcd(0x27, 20, 4);

Servo myservo2;
Servo myservo3;
Servo myservo4;

//使用するint型変数の宣言
int pos = 0;
int sensor_data = 255;
int old_sensor_data;
int threshold = 25;
int n=0;
//setup()ではサーボ割当ピン宣言と初期位置移動、センサの初期設定、LCDの初期設定を行う
void setup()
{
  Wire.begin();           //I2C通信開始
  Serial.begin(9600);//シリアル通信を9600bpsで初期化
  pinMode(2, OUTPUT);    //デジタルピン２を出力ピンにする

  myservo2.attach(9);    //サーボとピンの組み合わせの宣言 サーボ２，３，４をデジタルピン３，５，６に割り当てる
  myservo3.attach(5);
  myservo4.attach(6);

  myservo2.write(110);    //各サーボを初期位置に移動させる
  myservo3.write(30);
  myservo4.write(0);

  //センサの初期設定
  sensor.init();      //センサー初期化
  sensor.configureDefault();      //デフォルト設定の構成
  sensor.writeReg(VL6180X::SYSRANGE__MAX_CONVERGENCE_TIME, 30);     //8bitレジスタに書き込み
  sensor.writeReg16Bit(VL6180X::SYSALS__INTEGRATION_PERIOD, 50);    //16bitレジスタに書き込み　細かい設定の詳細は不明　なくても動くことは確認済み
  sensor.setTimeout(500);   //タイムアウトの秒数設定(500ms)
  delay(300);
  sensor.startInterleavedContinuous(100);   //連続インターリーブ測定開始

  //LCDの初期設定
  lcd.init();           //LCD初期化
  lcd.backlight();     //バックライト点灯
  lcd.setCursor(0, 0); //カーソル位置指定、（桁数、行数）で指定
  lcd.print("Start robot_arm"); //書き込み
  delay(500);
  //lcd.clear();    //画面のリセット

}

void loop()
{
  //把持位置にサーボを動かす
  for (pos = 30; pos < 50; pos += 1)
  {
    myservo3.write(pos);
    delay(15);
  }

  //把持位置に動いたら、センサの読み取りを行う
  //読み取りループ前の初期値獲得及び搬送後のセンサ値のリセットを兼ねる
  sensor_data = sensor.readRangeContinuousMillimeters();

  //センサ読み取りループ　センサ値が閾値threshold(25)以下になるまでループ
  while (sensor_data > threshold)
  {
    //センサを読み取り、sensor_data格納する。その値をLCDで表示する　LCD1行目に表示
    sensor_data = sensor.readRangeContinuousMillimeters();
    if (sensor_data != old_sensor_data)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("sensor_data:");
      lcd.setCursor(13, 0);
      lcd.print(sensor_data);

      //読み取ったデータを閾値と比べ、把持するべきかの表示　LCD2行目に表示
      if (sensor_data > threshold)
      {
        lcd.setCursor(0, 1);
        lcd.print("No catch");
      }
      else
      {
        lcd.setCursor(0, 1);
        lcd.print("Go catch");
      }
    }



    //タイムアウトチェック　タイムアウトが発生している場合にエラーの表示を行う　LDC3,4行目に表示
    if (sensor.timeoutOccurred())
    {
      lcd.setCursor(0, 2);
      lcd.print("Error");
      lcd.setCursor(0, 3);
      lcd.print("Time out");

      delay(500);

      //タイムアウト判定されたら、センサーとLCDの初期化及び初期設定をやり直す。
      sensor.init();      //センサー初期化
      sensor.configureDefault();      //デフォルト設定の構成
      sensor.writeReg(VL6180X::SYSRANGE__MAX_CONVERGENCE_TIME, 30);     //8bitレジスタに書き込み
      sensor.writeReg16Bit(VL6180X::SYSALS__INTEGRATION_PERIOD, 50);    //16bitレジスタに書き込み　細かい設定の詳細は不明　なくても動くことは確認済み
      sensor.setTimeout(500);   //タイムアウトの秒数設定(500ms)
      delay(300);
      sensor.startInterleavedContinuous(100);   //連続インターリーブ測定開始

      lcd.clear();    //画面のリセット
      lcd.init();           //LCD初期化
      lcd.backlight();     //バックライト点灯
      lcd.setCursor(0, 0); //カーソル位置指定、（桁数、行数）で指定
      lcd.print("Restart robot_arm"); //書き込み
      delay(500);
      
    }

    old_sensor_data = sensor_data;
    delay(50);
  }

  //センサ読み取りループ抜け　切り離し感知した時
  //アームを下げて、チャックの間に製品を入れる
  for (pos = 110; pos > 50; pos -= 1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(1000);
  digitalWrite(2, HIGH);    //デジタルピン2を通電させる　MOSFET➔リレーを通して電磁弁の切り替えが行われる
  lcd.setCursor(0, 2);      //LCDのカーソルを3行目（0➔1➔2だから）に移動
  lcd.print("Air chuck close");   //チャックが閉じている事を表示させる
  delay(500);

  //把持するために下げたアームを上げる
  for (pos = 50; pos < 110; pos += 1)
  {
    
    myservo2.write(pos);
    delay(15);
  }
  delay(1000);
  
  for (pos = 0; pos < 90; pos += 1)
  {
    myservo4.write(pos);
    delay(15);
  }
  delay(1000);

  //把持した製品を搬送する
    
    double x,y,L1,L2;
    float a,b,c,d;
    float theta1,theta2;
    float servotheta1,servotheta2;
    x = 20-2*n;
    y = 3.3-0.1*n;
    L1 = 14.9;
    L2 = 13.8;

    a =acos((sq(x)+sq(y)+sq(L1)-sq(L2))/(2*(L1)*sqrt(sq(x)+sq(y))))+atan(y/x);
    b =atan((y-L1*(sin(a)))/(x-L1*(cos(a))))-a;
    
    c = L1*cos(a)+L2*cos(b+a);
    d = L1*sin(a)+L2*sin(b+a);
    
    theta1 = degrees(a);
    theta2 = degrees(b);
    
    servotheta1 = 110-(90-theta1);
    servotheta2 = 30-(theta1+theta2);
    Serial.println(n);
    Serial.println(a);
    Serial.println(b);
    Serial.println(c);
    Serial.println(d);
    Serial.println(theta1);
    Serial.println(theta2);
    Serial.println(servotheta1);
    Serial.println(servotheta2);
    
    int i1,i2;
    i1 = servotheta1;
    i2 = servotheta2;
    
    for (pos = 110; pos > i1; pos -= 1)
    {
      myservo2.write(pos);
      delay(20);
    }
    
    for (pos = 30; pos < i2; pos += 1)
    {
      myservo3.write(pos);
      delay(20);
    }
    
    delay(5000);
    
    for (pos = i2; pos > 30; pos -= 1)
    {
      myservo3.write(pos);
      delay(20);
    }    
    
    for (pos = i1; pos < 110; pos += 1)
    {
      myservo2.write(pos);
      delay(20);
    }

    delay(5000);
  digitalWrite(2, LOW);
  lcd.setCursor(0, 2);
  lcd.print("Air chuck open ");   //LCDにチャックが開いていることを表示

  //アーム（アーム全体の向き制御用の4番サーボ）を待機用の初期位置に戻す。他サーボを初期位置に復帰済み
  for (pos = 90; pos > 0; pos -= 1)
  {
    myservo4.write(pos);
    delay(15);
  }
  delay(100);


  if(n<4)
   n = n+1;
  else;
   n=0;

}
