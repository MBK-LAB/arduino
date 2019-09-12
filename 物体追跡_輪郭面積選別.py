# use pyFirmata
# Copyright（c）2010、Tino de Bruijn

 
# pyFirmataを使ったFirmataにより、arduinoを制御


import sys
import time
import picamera
import cv2
import numpy as np
import io
#import serial
import pyfirmata

#windowName = 'image'
#cv2.namedWindow(windowName)

#firmataで制御するarduinoのポートを指定
board = pyfirmata.Arduino("/dev/ttyACM0")

#最初期窓サイズ（動画サイズと同じだと楽）
x = 0
y = 0
w = 500
h = 500
track_window = (x, y, w, h)

#サーボのピン設定
myservo_X = board.get_pin('d:11:s')
myservo_Y = board.get_pin('d:9:s')
myservo_Z = board.get_pin('d:3:s')


#カメラの初期位置と可動域限界設定（サーボの可動域と合わせる）
#X座標移動はサーボ４で、Y座標移動はサーボ2で行う
#サーボ3で奥行きのZ座標移動を予定している（現在は高い位置での固定）
#サーボ依存のための角度で設定する

#サーボ角度　小➔大　　反時計周り
x_setup = 90
x_max = 160
x_min = 20

#サーボ角度　小➔大　　上➔下　
y_setup = 50
y_max = 150
y_min = 30


#現在位置情報に初期位置を代入
x_now = x_setup
y_now = y_setup
z_now = 120
DELAY = 1


#サーボ操作用の簡易関数
def move_servoX(x):
        myservo_X.write(x)
        #board.pass_time(DELAY)

def move_servoY(y):
        myservo_Y.write(y)
        #board.pass_time(1)

def move_servoZ(z):
        myservo_Z.write(z)


#サーボを初期位置へ
move_servoX(x_now)
move_servoY(y_now)
move_servoZ(z_now)


# 撮影した動画から色マスクで輪郭を検出する
# min_areaより小さい面積の輪郭は排除
# 残った輪郭に対して外接矩形を作り、戻り値とする
def create_gaisetu(frame, track_window):
    x, y, w, h  = track_window
    #検出窓での区切り
    roi = frame[y:y+h, x:x+w]
    #窓内をBGR➔HSVに変換
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    #検出する色の設定（HSV表記にて最小最大を設定する）
    lower_blue = np.array([110., 80. ,50.])
    upper_blue = np.array([130.,255.,255.])
    #設定した条件にてマスクを作る
    mask = cv2.inRange(hsv_roi, lower_blue, upper_blue)
    #輪郭を検出する
    _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #面積による輪郭の選定
    min_area = 4000
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    #外接矩形の作成及び4点情報（左下の頂点の座標(x, y)、横の長さw、縦の長さh) の取得
    rect = []
    for contour in large_contours:
        rect = cv2.boundingRect(contour)
        x, y, w, h = rect
    #外接矩形の描写
    drow_contour = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 0), 2)
    #外接矩形の四点座標（rect）、描写(drow_contour)を戻り値とする
    return(rect, drow_contour)


# CamShiftを行う為の下準備
# 外接矩形内のヒストグラムの算出、正規化、及び精度設定行う    
def histogram(frame, rect):
    #引数として受け取った外接矩形の4点情報から検出窓の作成
    x, y, w, h = rect
    #x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    track_window = (x,y,w,h)
    #検出窓で画像を区切る
    roi = frame[y:y+h, x:x+w]
    #窓内をHSVに変換
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    #色によるマスクを行う
    lower_blue = np.array([110., 50., 50.])
    upper_blue = np.array([130., 255., 255.])
    mask = cv2.inRange(hsv_roi, lower_blue, upper_blue)
    #窓内のヒストグラムの算出
    roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0,180])
    #ヒストグラムの正規化
    cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    #アルゴリズムの繰り返し設定　回数と精度を背彫っていする
    term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    #戻り値として、検出窓、正規化したヒストグラム、アルゴリズムの繰り返し設定を戻す
    return track_window, roi_hist, term_crit


# CamShiftで物体を追跡する関数    
def tracking_movie(frame, track_window, roi_hist, term_crit):
    #動画全体を
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
    ret, track_window = cv2.CamShift(dst, track_window, term_crit)
    
    pts = cv2.boxPoints(ret)
    pts = np.int0(pts)

    #ptsの4座標から中心座標を算出
    center = pts[0]+pts[1]+pts[2]+pts[3]
    center = np.int0(center/4)
    print("中心", center)
    #print("x座標:",center[0])
    #print("y座標:",center[1])
    
    #求めた中心座標を中心とする円を描写
    img2 = cv2.circle(frame, (center[0],center[1]),5, (255, 255, 255), thickness=1)
    #追跡するべき色を囲った四角形の描写(ptsの４座標を頂点とする四角形の描写）
    img2 = cv2.polylines(frame, [pts], True, 255, 2)
    #描写した動画の表示
    cv2.imshow('SHOW MEANSHIFT IMAGE', img2)
    
    return(center)


#Picameraの準備
with picamera.PiCamera() as camera:
    #解像度、フレームレートの設定
    camera.resolution = (500, 500)
    camera.framerate = 20
    stream = io.BytesIO()
    time.sleep(1)

    #撮影、追跡を繰り返し動作させ続ける
    while True:
        #撮影➔OpenCVで編集可能な状態へ？
        #print("a")
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        #cv2.imshow('1',frame)    #この時点だと画像が表示されない
        frame = cv2.imdecode(frame, 1)
        #cv2.imshow('2',frame)     #カメラに写る画像のみ
        rect, drow_contour = create_gaisetu(frame, track_window)
        #cv2.imshow('gaisetu', drow_contour)
        if rect == []:
            print(rect)
            continue
            
            
        track_window, roi_hist, term_crit = histogram(frame, rect)

        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        frame = cv2.imdecode(frame, 1)
        cv2.imshow('2',frame)
        
        center = tracking_movie(frame,track_window, roi_hist, term_crit)
        track_window = x, y, w, h
        

        
#########追跡用のアーム動作開始#################################################################
#########追跡矩形の中心座標と映像の中心座標を一致させるように動作#####################################
#########動画サイズは(500, 500)なので、中心は(250, 250)となる（8/27現在）##########################
#########追跡矩形中心と動画中心の差を算出########################################################
        
        #正常に物体検出できているかチェック
        #物体が検出されていない時、追跡矩形の中心座標は(0, 0)となり、映像中心座標との差が(-250, -250)となる
        #座標差が(-250, -250)になった場合に追跡関数の再呼び出しを行い、座標差の算出をやり直す
        
      
        
        x_dif = center[0] - 250
        y_dif = center[1] - 250
        
        """
        if x_dif == -250 and y_dif == -250:
            continue
        """

        #アームが一気に動きすぎないように座標差を小さくして、中心方向への動きを算出
        x_move = x_now - x_dif*0.01
        y_move = y_now + y_dif*0.01
        
        #可動域外にいかないように、設定最低値と最大値を超えていたら書き換える
        if x_move > x_max:
                x_move = x_max
        elif x_move < x_min:
                x_move = x_min
        if y_move > y_max:
                y_move = y_max
        elif y_move < y_min:
                y_move = y_min
                
        
        #算出時に動きすぎないように修正したが、それでも一気に10°以上の変更があった場合は動かないようにする制限
        #プログラムを動かして大きく動いてしまう時のチェク用（普段はコメントアウト）
        #現在この部分のコード入れるとエラーを吐く
        """
        if abs(x_move - x_now > 10):
                x_move = x_now
        if abs(y_move - y_now > 10):
               y_move = y_now
        
        """
        #座標関連情報の表示
        print(x_now)
        print(x_dif)
        print(y_now)
        print(y_dif)
        #print(str(x_move))
        x_move = int(x_move)
        y_move = int(y_move)
        
        if x_move == x_now:
            x_move = x_now - x_dif*0.05
            x_move = int(x_move)
            
        if y_move == y_now:
            y_move = y_now + y_dif*0.05
            y_move = int(y_move)
            
        print("Xサーボ:",x_move)
        print("Yサーボ:",y_move)
        
        #Xの新角度、Yの新角度をfirmataで制御
        move_servoX(x_move)
        #time.sleep(0.2)
        move_servoY(y_move)

        #移動先 x_move, y_moveを現在位置に更新 
        x_now = x_move
        y_now = y_move
        
        
        
        #プログラム終了条件（’q’が入力されるとwhileループの終了）
        k = cv2.waitKey(1)
        #print(y_now)
        #print(y_dif)
        if k == ord('q'):
            x_move = x_setup
            y_move = y_setup
            
            move_servoX(x_move)
            time.sleep(1)
            move_servoY(y_move)
            time.sleep(1)
            
            
            cv2.destroyAllWindows()
            board.exit()
            break
            
            #アームの初期位置に戻してからの終了を試みた
            #現状上手くいかなかったために凍結
            
            
        """
            x_move = x_setup
            y_move = y_setup
            move_servoX(x_move)
            move_servoY(y_move)
            time.sleep(3)
        """
            

#全ての表示ウィンドウを削除

#board.exit()
