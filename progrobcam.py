import dbus
import dbus.mainloop.glib
from gi.repository import GObject as gobject
from gi.repository import GLib
import time
import cv2 as cv
import numpy as np

capture = None
loop = None

data = []

proxSensorsVal = [ 0, 0, 0, 0, 0, 0, 0 ]
proxGroundVal = [ 0, 0 ]
cX=380
cY=200
def Quit():
    motor(0,0)
    loop.quit ()

### fonctions de gestion du robot

def get_variables_reply_ground(r):
    global proxGroundVal
    proxGroundVal=r

def get_variables_error_ground(e):
    print ('error:')
    print (e)
    Quit()

def get_variables_reply(r):
    global proxSensorsVal
    proxSensorsVal=r
 
def get_variables_error(e):
    print ('error:')
    print (e)
    Quit()
 
def motor(pwrLeft,pwrRight,duration=None) :
    network.SetVariable("thymio-II", "motor.left.target", [pwrLeft])
    network.SetVariable("thymio-II", "motor.right.target", [pwrRight])
    if duration is not None:
        time.sleep(duration)
        network.SetVariable("thymio-II", "motor.left.target", [0])
        network.SetVariable("thymio-II", "motor.right.target", [0])

def robotCallback():
    global data, cX, cY
    network.GetVariable("thymio-II", "prox.horizontal",reply_handler=get_variables_reply,error_handler=get_variables_error)
    network.GetVariable("thymio-II", "prox.ground.delta",reply_handler=get_variables_reply_ground,error_handler=get_variables_error_ground)
    # comportement reflexe en tenant compte des capteurs
    # si pas comportement reflexe, IA en utilisant les données de la camera
        
    if cX < 320 :
        if cY<180:
            motor(300,150)
        elif cY<360 and cY>180:
         motor(300,0)
        elif cY>360:
         motor(300,-300)


    elif cX < 640 and cX>320:
        if cY<180:
         motor(500,500)
        elif cY<360 and cY>180:
            motor(0,0)
        elif cY>360:
            motor(-300,-300)


    elif cX > 640:
        if cY<180:
         motor(150,300)
        elif cY<360 and cY>180:
         motor(0,300)
        elif cY>360:
          motor(-300,300)
    """
    if proxSensorsVal[0]<1000 and proxSensorsVal[1]<1000 and proxSensorsVal[2]<1000 and proxSensorsVal[3]<1000 and proxSensorsVal[4]<1000 :
        motor(300,300) 
        if ((proxSensorsVal[5] + proxSensorsVal[6])/2)<2000 :
            motor(600,600)

    if proxSensorsVal[0]>=1000 and proxSensorsVal[2]<1000:
           motor(300,50) 
    if proxSensorsVal[2]>=1000 :
        motor(-300,300) 

    if proxSensorsVal[4]>=1000 and proxSensorsVal[2]<1000:
           motor(50,300) 
    """
    return True

### fonctions de gestion de la caméra

def cameraCallback():
    global capture, loop
    global data, cX, cY
    ret, frame = capture.read ()
    if frame is not None:
        # calculs sur l'image
        _, frame = capture.read()
        frame = cv.resize(frame,(960,540),fx=0,fy=0, interpolation = cv.INTER_CUBIC)
        blurred_frame=cv.GaussianBlur(frame, (5,5), 0)
        hsv=cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        lower_blue=np.array([0,0,80])
        upper_blue=np.array([50,50,255])
        mask=cv.inRange(blurred_frame, lower_blue, upper_blue)

        contours, _= cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
            
        for contour in contours :
            area = cv.contourArea(contour)
            print(area)
            if area>5000:
                cv.drawContours(frame, contour, -1, (0,0,255),3)
                M = cv.moments(contour)
                if M["m00"] is not None:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    print("posX= ", cX, " posY= ",cY)
                    cv.circle(frame, (cX, cY), 7, (255, 255, 255), -1)
                    cv.putText(frame, "center", (cX - 20, cY - 20),
                    cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        cv.line(frame, (0,180), (960,180), [255,255,255], 2)
        cv.line(frame, (0,360), (960,360), [255,255,255], 2)
        cv.line(frame, (320,0), (320,540), [255,255,255], 2)
        cv.line(frame, (640,0), (640,540), [255,255,255], 2)
        #cv.imshow("Frame",frame)
        #cv.imshow("Mask", mask)

        # initialisation de data (transmission de données entre la camera et le robot)
        cv.imshow("view",frame)
        if cv.waitKey(10) & 0xFF == ord('q'):
            Quit()
    return True

### programme principal

if __name__ == '__main__':
    # initialisation du robot
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    network = dbus.Interface(bus.get_object('ch.epfl.mobots.Aseba', '/'), dbus_interface='ch.epfl.mobots.AsebaNetwork')

    # initialisation de la caméra
    capture = cv.VideoCapture(0)

    #GObject loop
    print ('starting loop')
    loop = GLib.MainLoop ()
    handler = GLib.timeout_add (100, robotCallback) # 10 times per second
    handlec = GLib.timeout_add (33, cameraCallback) # 30 time par second
    loop.run()

