import time
import picamera
import cv2
import numpy as np
import io
import serial

#windowName = 'image'
#cv2.namedWindow(windowName)

#arduinoとシリアル通信開始
ser = serial.Serial('/dev/ttyACM0', 57600)

#最初期窓サイズ（動画サイズと同じだと楽）
x = 0
y = 0
w = 500
h = 500
track_window = (x, y, w, h)

#カメラの初期位置と可動域限界設定（サーボの可動域と合わせる）
#X座標移動はサーボ４で、Y座標移動はサーボ３で行う（他サーボは固定、位置はarduinoので指定済みとする)
#サーボ依存のための角度で設定する
#８/27現在未調整
x_setup = 90
x_max = 160
x_min = 20

y_setup = 110
y_max = 130
y_min = 60

#現在位置情報に初期位置を代入
x_now = x_setup
y_now = y_setup


#撮影した動画から物体追跡するための関数　　物体検出矩形の中心点を返す
def tracking_movie(frame, track_window):
    #検出窓での区切り
    roi = frame[y:y+h, x:x+w]
    #窓内をBGR➔HSVに変換
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    #検出する色の設定（HSV表記にて最小最大を設定する）
    lower_blue = np.array([110., 50.,50.])
    upper_blue = np.array([130.,255.,255.])
    #設定した条件にてマスクを作る
    mask = cv2.inRange(hsv_roi, lower_blue, upper_blue)
    #変換した窓内をマスクした物でヒストグラムを算出する（要：引数に対する検証）
    roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0,180])
    #roi_hist = cv2.calcHist([hsv_roi], [0], mask, [256], [0,256])
    #算出したヒストグラムを正規化
    cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    #繰り返し処理の終了条件（要検証）
    term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        
        
    
    #映像全体のBGR➔HSV変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #全体映像を算出したヒストグラムを用いて逆投影
    dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180], 1)
    #dst = cv2.calcBackProject([hsv],[0,1],roi_hist,[0,180,0,256], 1)
    #meanshift法を用いて、追跡
    ret, track_window = cv2.CamShift(dst, track_window, term_crit)
        
    pts = cv2.boxPoints(ret)
    pts = np.int0(pts)
    

    #ptsの4座標から中心座標を算出　img2 = c
    center = pts[0]+pts[1]+pts[2]+pts[3]
    center = np.int0(center/4)
    print("中心",center)
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
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        #cv2.imshow('1',frame)    #この時点だと画像が表示されない
        frame = cv2.imdecode(frame, 1)
        #cv2.imshow('2',frame)     #カメラに写る画像のみ
        

        center = tracking_movie(frame,track_window)
        
        #追跡用のアーム動作開始
        #追跡四角の中心座標と映像の中心座標を一致させるように動作
        #動画サイズは(500, 500)なので、中心は(250, 250)となる（8/27現在）
        #追跡四角中心と動画中心の差を算出
        while True:
           x_dif = center[0] - 250
           y_dif = center[1] - 250
           print(x_dif)
           if x_dif == -250 and y_dif == -250:
                
                center = tracking_movie(frame,track_window)
           else:
                break
        x_move = x_now - x_dif*0.05
        y_move = y_now + y_dif*0.05
        #可動域外にいかないようにする
        if x_move > x_max:
                x_move = x_max
        elif x_move < x_min:
                x_move = x_min
        if y_move > y_max:
                y_move = y_max
        elif y_move < y_min:
                y_move = y_min
        
        if abs(x_move - x_now > 10):
                x_move = x_now
        if abs(y_move - y_now > 10):
                y_move = y_now
        print(x_now)
        print(x_dif)
        print(y_now)
        print(y_dif)
        print("Xサーボ:",x_move)
        print("Yサーボ:",y_move)
        #print(str(x_move))
        #Xの新角度、Yの新角度を通信する
        move = []
        move.append(int(x_move))
        move.append(int(y_move))
        #print(move)
        ser.write((str(move[0])+","+str(move[1])+'\n').encode('utf-8'))
        #print(str(move))
        #time.sleep(0.8)
        
        """
        arduino_data = ser.readline()
        arduino_data = arduino_data.strip().decode('utf-8')
        print(arduino_data)
        """
        

        
        while True:
                arduino_data = ser.readline()
                arduino_data = arduino_data.strip().decode('utf-8')
                print(arduino_data)	
                if(arduino_data == "end"):
                        print("ok")
                        break
        
        

        
        """
        arduino_data = ser.readline()
        arduino_data = arduino_data.strip().decode('utf-8')
        print(arduino_data)
        """
        
        
        """
        while True:
                arduino_data = ser.readline()
                arduino_data = arduino_data.strip().decode('utf-8')
                print(arduino_data)	
                if(arduino_data == '1'):
                        print("ok")
                        break
        
        """
        
        #移動先 x_move, y_moveを現在位置に更新 
        x_now = x_move
        y_now = y_move
        
        
        
        #プログラム終了条件（’q’が入力されるとwhileループの終了）
        k = cv2.waitKey(1)
        if k == ord('q'):
            """
            x_move = 90
            y_move = 90
            move.append(int(x_move))
            move.append(int(y_move)) 
            ser.write((str(move[0])+","+str(move[1])+'\n').encode('utf-8'))  
            """
            break

#全ての表示ウィンドウを削除
cv2.destroyAllWindows()
