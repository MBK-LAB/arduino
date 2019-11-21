//例文に他の必要プログラムを足して、本実装スケッチの雛形の作成
//インターリーブ連続モードの例文との組み合わせ
//センサーの動作テストの結果としてシングルショットで問題無いようなら、簡易な構文で済むシングルショットに変更
//必要な動作は　サーボの動作、センサーの読み取り、読み取った内容をトリガーにした電磁弁の制御


//サーボ,I2C通信,VL6180Xのためのライブラリをインクルードする
#include <Servo.h>
#include <Wire.h>
#include <VL6180X.h>

VL6180X sensor;  //コンストラクタ
Servo myservo1;
int pos;
int senser_data;
int threshold;


void setup()
{
  Serial.begin(9600);   //シリアル通信の開始
  Wire.begin();     //I2C通信の開始

  pinMode(2, OUTPUT);   //出力ピンの設定(MOSFET制御用)
  myservo1.attach(5);   //サーボの設定
  
  sensor.init();    //センサーに必要な情報のロードして初期化
  sensor.configureDefault();    //デフォルト動作のいくつかの設定を構成する


  //8ビットセンサーレジスタに書き込み
  //1つ目の引数：VL6180X::SYSRANGE__MAX_CONVERGENCE_TIMEはライブラリで指定されているレジスタアドレス
  //2つ目の引数：30が書き込む数値
  //最大収束時間？を30msに設定(デフォルトは49ms)➔測定にかける最大時間の定義だと思われる
  sensor.writeReg(VL6180X::SYSRANGE__MAX_CONVERGENCE_TIME, 30);
  
  //16ビットセンサーレジスタに書き込み
  //引数はレジスタアドレスと書き込む数値
  //ALS(光センサー)の積分時間(感知する光強度に影響を与えるセンサーの起電力累積時間)➔ALS連続の測定間に用いる時間遅延の決定
  sensor.writeReg16Bit(VL6180X::SYSALS__INTEGRATION_PERIOD, 50);

  //タイムアウト時間の設定　単位はms　0にするとタイムアウト無効
  sensor.setTimeout(500);

  //連続モードの停止、すでにアクティブな場合のために行う
  sensor.stopContinuous();
  //上文がシングルショット測定のトリガーとなった場合のdealy
  delay(300);

  //100ms周期のインターリーブ連続モードを開始する
  //10msの解像度、デフォルト周期は500ms
  //現状モードの細かいことは不明
  sensor.startInterleavedContinuous(100);
}

void loop() 
{
  //把持位置へアームを移動させる
  for(pos = 50; pos < 110; pos += 1)
  {
    myservo1.write(pos);
    delay(15);
  }
  Serial.println("Servo comp");
  delay(500);

  //チャック閉タイミング用のセンサーの読み取り
  //距離センサーの値senser_dataが基準値thresholdより小さくなる(切断部がセンサーに近くなる)まで
  //センサーの読み取りを繰り返す
  threshold = 20;
  senser_data = 255;
  while(senser_data > threshold)
  {
    //センサーの値を読み取ってシリアルモニターに表示させている
    //sensor.readRangeContinuousMillimeters()は連続モードがアクティブな場合、スケーリング範囲を考慮してミリメートル単位で値を返す
    //timeoutOccurred()は最後にこの関数が呼び出されてからタイムアウトが発生したかを示す
    //if(sensor.timeoutOccurred())なので、タイムアウトが起こった場合に、if条件が満たされるようになっている。
    Serial.print("tRange:");
    Serial.print(sensor.readRangeContinuousMillimeters());
    if(sensor.timeoutOccurred())
    {Serial.print("TIMEOUT");}
    Serial.println();

    senser_data = sensor.readRangeContinuousMillimeters();
  }

  delay(100);

  //whileループを抜けたのでMOSFETの制御で電磁弁の切り替え、製品を把持する
  digitalWrite(2, HIGH);    //MOSFETのG(ゲート)に電流を流す
  Serial.println("ON");

  
  //把持した製品を搬送する
  for(pos = 110; pos > 50; pos -= 1)
  {
    myservo1.write(pos);
    delay(15);
  }
  delay(500);

  digitalWrite(2, LOW); 
  Serial.println("OFF");
  //arduinoはループ制御なので最初の把持位置まで移動に戻る
}
