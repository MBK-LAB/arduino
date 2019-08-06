

//4軸動作テスト用プログラム
//arduinoのスケッチは、void loop()の動作をループし続ける


//サーボライブラリのインクルード
#include <Servo.h> 

//サーボの宣言
Servo handservo;    //グリッパーのサーボ
Servo myservo1;     //グリッパー取り付け部のサーボ
Servo myservo2;     //アーム上軸
Servo myservo3;     //アーム下軸
Servo myservo4;     //アーム台座サーボ

//変数の宣言
int pos; //サーボ動作用の変数
int setupif=0;  //サーボ位置リセット関数の管理用
int hand_servo, servo1, servo2, servo3, servo4; //サーボ角度読み込み用変数
int myspeed;  //サーボリセット時の移動速度変数


//サーボのリセット用の関数（servorest)
void servoreset()
{
   hand_servo=handservo.read();
   servo1=myservo1.read();
   servo2=myservo2.read();
   servo3=myservo3.read();
   servo4=myservo4.read();

   
   myspeed=500;
   for(pos=0;pos<=myspeed;pos+=1)
   {
    handservo.write(int(map(pos,1,myspeed,hand_servo,10)));
    delay(500);
    myservo1.write(int(map(pos,1,myspeed,servo1,20)));
    delay(500);
    myservo2.write(int(map(pos,1,myspeed,servo2,80)));
    delay(500);
    myservo3.write(int(map(pos,1,myspeed,servo3,100)));
    delay(500);
    myservo4.write(int(map(pos,1,myspeed,servo4,60)));  
    delay(500);
   }
}



//サーボのピン設定　サーボ番号は先端から順にhand+1〜3番軸設定　ピンは3,5,6,11(PWMの使えるピン)
void setup() 
{ 
  handservo.attach(3);
  myservo1.attach(5);   
  myservo2.attach(6);
  myservo3.attach(9);
  myservo4.attach(11);


  handservo.write(10);
  myservo1.write(160);   
  myservo2.write(30);
  myservo3.write(110);
  myservo4.write(60);

} 
 

//動作プログラム
void loop() 
{ 
  
  //アーム初期位置関数呼び出し（if文管理）
  if(setupif=0)
  {servoreset();}
  //一度で終了のためif条件を崩す
  setupif=1;
  delay(3000);
  
//////////////////////////////////////////////////////////////////////////////
///////   初期位置から持ち上げるまでまで　　///////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

  //アームを倒す1（3番サーボ動作）
  for(pos=110; pos>80; pos-=1)
  {
     myservo3.write(pos);
     delay(15);
  }
  delay(500);
  
  //アームを倒す2（2番サーボ動作）
  for(pos=30; pos<68; pos+=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);

  //グリッパーを閉じる（handサーボ動作）
  for(pos=10; pos<150; pos+=1)  
  {                                  
    handservo.write(pos);             
    delay(5);                       
  } 
  delay(500);
  
  //アームを持ち上げる1（2番サーボ動作）
  for(pos = 68; pos>30; pos-=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);

  //アームを持ち上げる2（３番サーボ動作）
  for(pos=80; pos<110; pos+=1)
  {
    myservo3.write(pos);
    delay(15);
  }
  delay(500);

//////////  持ち上げ終了  /////////////////////////////


/////////////////////////////////////////////////////
/////////  向き変更開始  /////////////////////////////
////////////////////////////////////////////////////

  //グリッパーの向き変更（1番サーボ動作）
  for(pos=160; pos>20; pos-=1)
  {
    myservo1.write(pos);
    delay(15);
  }
  delay(500);

  //アームの向き変更(4番サーボの動作)
  for(pos=60; pos<120; pos+=1)
  {
    myservo4.write(pos);
    delay(15);
  }
  delay(500);

/////////  向き変更終了  /////////////////////////////////


////////////////////////////////////////////////////////
////////  下ろす動作と初期位置への戻り  ////////////////////
////////////////////////////////////////////////////////


  //アームを倒す２（3番サーボ動作）
  for(pos=110; pos>80; pos-=1)
  {
     myservo3.write(pos);
     delay(15);
  }
  delay(500);

  //アームを倒す1（2番サーボ動作）
  for(pos=30; pos<68; pos+=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);

  //グリッパーを開く（ハンドサーボ動作）
  for(pos = 150; pos>10; pos-=1)
  {
    handservo.write(pos);
    delay(5);
  }
  delay(500);

  //アームを持ち上げる1（2番サーボ動作）
  for(pos = 68; pos>30; pos-=1)
  {
    myservo2.write(pos);
    delay(15);
  }
  delay(500);

  //アームを持ち上げる2（３番サーボ動作）
  for(pos=80; pos<110; pos+=1)
  {
    myservo3.write(pos);
    delay(15);
  }
  delay(500);
  

  //グリッパーの向き変更（1番サーボ動作）
  for(pos = 20; pos<160; pos+=1)
  {                                
    myservo1.write(pos);              
    delay(15);                        
  } 
  delay(500);

  //アームの向き変更(4番サーボの動作)
  for(pos=120; pos>60; pos-=1)
  {
    myservo4.write(pos);
    delay(15);
  }
  delay(500);

///////  初期位置への戻り終了  //////////////////
} 
