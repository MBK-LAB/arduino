# use pyFirmata
# Copyright（c）2010、Tino de Bruijn

 
# pyFirmataを使ったFirmataにより、arduinoを制御
# 色マスクからの輪郭検出を行い、輪郭面積による条件分けを行う

###import一覧############################################################
########################################################################
import sys
import time
import picamera
import cv2
import math
import numpy as np
import io
#import serial
import pyfirmata


###設定一覧###############################################################
########################################################################

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

#Z軸（奥行き）移動用　検出窓面積
#CamShiftが更新する検出窓面積がS_1と一致するようにZ軸が動く
S_1 = 50000

#追跡完了用カウント
end = 0

#サーボのピン設定
myservo_X = board.get_pin('d:9:s')
myservo_Y = board.get_pin('d:11:s')
myservo_Z = board.get_pin('d:5:s')


#カメラの初期位置と可動域限界設定（サーボの可動域と合わせる）
#X座標移動はサーボ４で、Y座標移動はサーボ2で行う
#サーボ3で奥行きのZ座標移動
#サーボ依存のための角度で設定する
#時計反時計は向かってグリッパーが右の時

#サーボ角度　小➔大　　反時計周り
x_setup = 90
x_max = 160
x_min = 20

#サーボ角度　小➔大　　上➔下　
y_setup = 60
y_max = 130
y_min = 40

#サーボ角度　小⇛大　反時計
z_setup = 110
z_max = 130
z_min = 50

#現在位置情報に初期位置を代入
x_now = x_setup
y_now = y_setup
z_now = z_setup



###関数##################################################################
########################################################################

#サーボ操作用の簡易関数
def move_servoX(x_now, x_move):
    if x_now < x_move:
        move_range = x_move - x_now + 1
        for i in range(move_range):
            angle = x_now + i
            myservo_X.write(angle)
            i += 1
            time.sleep(0.02)
    
    else:
        move_range = x_now - x_move + 1
        for i in range(move_range):
            angle = x_now - i
            myservo_X.write(angle)
            i += 1
            time.sleep(0.02)

def move_servoY(y_now, y_move):
    if y_now < y_move:
        move_range = y_move - y_now + 1
        for i in range(move_range):
            angle = y_now + i
            myservo_Y.write(angle)
            i += 1
            time.sleep(0.02)
    
    else:
        move_range = y_now - y_move + 1
        for i in range(move_range):
            angle = y_now - i
            myservo_Y.write(angle)
            i += 1
            time.sleep(0.02)

def move_servoZ(z_now, z_move):
    if z_now < z_move:
        move_range = z_move - z_now + 1
        for i in range(move_range):
            angle = z_now + i
            myservo_Z.write(angle)
            i += 1
            time.sleep(0.02)
    
    else:
        move_range = z_now - z_move + 1
        for i in range(move_range):
            angle = z_now - i
            myservo_Z.write(angle)
            i += 1
            time.sleep(0.02)


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
    for cnt in contours:
        area =cv2.contourArea(cnt)
    #print("輪郭面積", aa)
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
    #動画全体をHSV変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #ヒストグラムの逆投影
    dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
    #CamShift で物体追跡させる
    ret, track_window = cv2.CamShift(dst, track_window, term_crit)
    #CamShiftで作った検出窓の座標を入手
    pts = cv2.boxPoints(ret)
    pts = np.int0(pts)
    #print(pts)
    #print("Cam_window", track_window)
    S_2 = track_window[2] * track_window[3]
    #print("window_size", area)
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
    #追跡窓の中心座標を戻す
    return(center, S_2)


###メインプログラム########################################################
########################################################################

#アームを初期位置へ
myservo_X.write(x_now)
myservo_Y.write(y_now)
myservo_Z.write(z_now)

#アームの初動調整
move_servoZ(z_now, 120)
move_servoZ(120, 60)
move_servoZ(60, z_now)

move_servoX(x_now, 110)
move_servoX(110, 70)
move_servoX(70, x_now)

move_servoY(y_now, 100)
move_servoY(100, 40)
move_servoY(40, y_now)




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
        #print("a")　#ループしているかチェック用
        #動画からフレームを取り出す
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        #cv2.imshow('1',frame)    #この時点だと画像が表示されない
        frame = cv2.imdecode(frame, 1)
        #cv2.imshow('2',frame)     #カメラに写る画像のみ
        
        #外接矩形作成関数の呼び出し
        rect, drow_contour = create_gaisetu(frame, track_window)
        #cv2.imshow('gaisetu', drow_contour)    #外接矩形を描写した動画の表示
        # rect == [] つまり外接矩形が作成できなかった時は、全て処理を飛ばして最初に戻す
        if rect == []:
            print(rect)
            continue
            
        #ヒストグラム用の関数の呼び出し    
        track_window, roi_hist, term_crit = histogram(frame, rect)

        #動画からフレーム取り出す
        camera.capture(stream, format="jpeg", use_video_port=True)
        frame = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        stream.seek(0)
        frame = cv2.imdecode(frame, 1)
        cv2.imshow('2',frame)
        
    #本来はCamShiftが検出窓を更新するため、検出窓のサイズを初期化する必要はない
    #何らかの理由でトラッキングがはずれた時に輪郭面積による選別を行いたいため、検出後に窓サイズの初期化、及び輪郭検出から繰り返すようにしている
    #この条件の場合CamShiftである必要がないと思われるが、他パターンの動作比較も含めてCamShiftを使用している
        #物体追跡用の関数の呼び出し
        center, S_2 = tracking_movie(frame,track_window, roi_hist, term_crit)
        #検出窓を初期サイズに戻す
        track_window = x, y, w, h
        print(S_2)
        

        
#########追跡用のアーム動作開始#################################################################
#########追跡矩形の中心座標と映像の中心座標を一致させるように動作#####################################
#########動画サイズは(500, 500)なので、中心は(250, 250)となる（8/27現在）##########################
#########追跡矩形中心と動画中心の差を算出########################################################
        
        #正常に物体検出できているかチェック
        #物体が検出されていない時、追跡矩形の中心座標は(0, 0)となり、映像中心座標との差が(-250, -250)となる
        #座標差が(-250, -250)になった場合に追跡関数の再呼び出しを行い、座標差の算出をやり直す
        
        #X軸、Y軸の移動先算出
        #検出窓の中心座標と映像の中心座標の差を算出
        x_dif = center[0] - 250
        y_dif = center[1] - 250
        
        """
        if x_dif == -250 and y_dif == -250:
            continue
        """

        #アームが一気に動きすぎないように座標差を小さくして、中心方向への動きを算出
        #一気に大きく動かないように中心座標同士の差に倍率を加える
        x_move = x_now - x_dif*0.02
        y_move = y_now + y_dif*0.02
        
        #Z軸方向の移動を算出
        #物までの理想距離 L1 を算出したい時、L1における物の面積S1、基準の距離L2、L2における物の面積S2が既知ならば
        #L1 = √S2 / √S1 * L2で算出できる
        #ここで算出されるのはサーボの数値ではなく、物体とカメラの間の理想距離
        #よって、√S2 / √S1の比率でZ軸サーボを動かす
        z_dif = math.sqrt(S_2) / math.sqrt(S_1) - 1
        z_move = z_now + z_dif * 10  
        
            
        #算出時に動きすぎないように修正したが、それでも一気に10°以上の変更があった場合は動かないようにする制限
        #プログラムを動かして大きく動いてしまう時のチェク用（普段はコメントアウト）
        #現在この部分のコード入れるとエラーを吐く
        """
        if abs(x_move - x_now > 10):
            x_move = x_now
        if abs(y_move - y_now > 10):
            y_move = y_now
        if abs(z_move - z_now >10):
            #z_move = z_now + z_dif * 5 
        """
        #現在角度now、移動算出用差dif の表示用
        """
        #座標関連情報の表示
        print("現在Xサーボ角度", x_now)
        print("現在Xサーボ角度", x_dif)
        print("現在Xサーボ角度", y_now)
        print("現在Xサーボ角度", y_dif)
        print(z_dif)
        print(z_move)
        #print(str(x_move))
        """
        
        #x_moveの整数化　サーボをpyFirmataで動かす場合、サーボを整数角度による操作となる
        x_move = int(x_move)
        y_move = int(y_move)
        z_move = int(z_move)
        
        #x_move,y_moveの算出の際の倍率が低いために中心付近に近づくと止まる可能性がある
        #倍率が小さい方がアームの動作速度が下がるために安定度が高いため、そちらを優先している
        #現在サーボ角度 x_now, y_now と　移動サーボ角度 x_move, y_moveが一致した場合、倍率を高くして再算出する
        """
        if x_move == x_now:
            x_move = x_now - x_dif*0.05
            x_move = int(x_move)
            
        if y_move == y_now:
            y_move = y_now + y_dif*0.05
            y_move = int(y_move)
        """
        #可動域外にいかないように、設定最低値と最大値を超えていたら書き換える
        if x_move > x_max:
                x_move = x_max
        elif x_move < x_min:
                x_move = x_min
        if y_move > y_max:
                y_move = y_max
        elif y_move < y_min:
                y_move = y_min
        if z_move > z_max:
                z_move = z_max
        elif z_move < z_min:
                z_move = z_min
        
        #サーボの移動先角度の表示    
        print("Xサーボ:",x_move)
        print("Yサーボ:",y_move)
        print("Zサーボ:",z_move)
        
        #Xの新角度、Yの新角度をfirmataで制御
        move_servoX(x_now, x_move)
        #time.sleep(0.2)    #アーム速度低、遅延なしの方が安定するのでコメントアウトに変更　条件しだいに戻せるようにそのまま
        move_servoY(y_now, y_move)
        move_servoZ(z_now, z_move)
        
        #追跡完了用のカウント(end)
        if x_move == x_now and y_move == y_now and z_move == z_now :
            end += 1
        else:
            end = 0
        print(end)
        

        #移動先 x_move, y_moveを現在位置に更新 
        x_now = x_move
        y_now = y_move
        z_now = z_move
        
        #追跡完了の判断条件 全サーボ移動なし×10
        #初期位置にセットアップ
        #指定されたアーム動作を行う
        #初期位置に戻る
        if end > 9 :
            #追跡が完了したことの表示、追跡用のウィンドウの削除
            print("追跡終了")
            cv2.destroyAllWindows()
            
            #移動先を初期位置へ設定
            print("初期値へ戻る")
            x_move = x_setup
            y_move = y_setup
            z_move = z_setup
            
            #初期位置へ移動
            move_servoX(x_now, x_move)
            move_servoY(y_now, y_move)
            move_servoZ(z_now, z_move)
            print("初期位置に到達")
            
            #現在位置を更新          
            x_now = x_move
            y_now = y_move
            z_now = z_move
            
            #一拍置く
            time.sleep(3)
            
            #指定動作開始
            print("動作開始")
            #各軸の移動先角度の設定
            x_move = 60
            y_move = 90
            z_move = 60
            #アーム動作
            move_servoX(x_now, x_move)
            move_servoY(y_now, y_move)
            move_servoZ(z_now, z_move)
            #元の位置に戻る
            time.sleep(1)
            move_servoZ(z_move, z_now)
            time.sleep(1)
            move_servoY(y_move, y_now)
            time.sleep(1)
            move_servoX(x_move, x_now)
            time.sleep(1)
            #whileループの最初に戻る
        
        
        #プログラム終了条件（’q’が入力されるとwhileループの終了）
        k = cv2.waitKey(1)
        if k == ord('q'):
            #移動先に初期位置を設定
            x_move = x_setup
            y_move = y_setup
            z_move = z_setup
            
            #初期位置にサーボを動かす
            move_servoX(x_now, x_move)
            time.sleep(1)
            move_servoY(y_now, y_move)
            time.sleep(1)
            move_servoZ(z_now, z_move)
            time.sleep(1)
            
            #動画取得、Firmataの終了
            cv2.destroyAllWindows()
            board.exit()
            #whileループから脱出
            break
            
            

#全ての表示ウィンドウを削除

#board.exit()
