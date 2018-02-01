import RPi.GPIO as GPIO
from threading import Thread
import socket
import time
import netifaces
import threading
import math

INPUT = 0
OUTPUT = 1
PWM = 2
LEFT = 18
RIGHT = 23
ECHO = 2
TRIG = 25

lst_of_pts = ''

ultra_sonic_dist = 0

left_holes = 0
left_opaques = 0
left_ratio = 0
left_wheel_dirn = 1
right_holes = 0
right_opaques = 0
right_ratio = 0
right_wheel_dirn = 1

increaser = 0.025  # increase 1/40 everytime hole/opaque is detected

lrotations = 0  # count of total rotation of wheel
rrotations = 0
sign = lambda x: (1, -1)[x < 0]  # function to return sign of a number

path_client = None

def setup_gpio():
    global pwm0_LB, pwm1_LF, pwm2_RB, pwm3_RF
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(4, GPIO.OUT)  # these are for motor drivers
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)
    GPIO.setup(22, GPIO.OUT)

    GPIO.setup(18, GPIO.IN)  # these are for wheel encoders
    GPIO.setup(23, GPIO.IN)

    GPIO.setup(2, GPIO.IN)  # ultrasonic input,, echo
    GPIO.setup(25, GPIO.OUT)  # ultrasonic output,, trigger

    pwm0_LB = GPIO.PWM(27, 200)  # pwm initialization with freuency 200
    pwm0_LB.start(0)
    pwm1_LF = GPIO.PWM(22, 200)
    pwm1_LF.start(0)
    pwm2_RB = GPIO.PWM(4, 200)
    pwm2_RB.start(0)
    pwm3_RF = GPIO.PWM(17, 200)
    pwm3_RF.start(0)

    if GPIO.input(RIGHT):  # check for initial inputs to the encoders
        print('initially Right = {} on opaque'.format(RIGHT))
    else:
        print('initially Right = {} on hole'.format(RIGHT))

    if GPIO.input(LEFT):
        print('initially Left = {} on opaque'.format(LEFT))
    else:
        print('initially Left = {} on hole'.format(LEFT))
    pass


def rotateLeftWheel(speed):  # function to rotate left wheel
    global pwm0_LB, pwm1_LF, left_wheel_dirn
    # speed = speed * 0.7
    if abs(speed) > 100:
        print('value of speed should be in between -100 and +100')
        return
    if speed > 0:
        pwm0_LB.ChangeDutyCycle(0)
        pwm1_LF.ChangeDutyCycle(speed)
        left_wheel_dirn = 1
    elif speed < 0:
        pwm1_LF.ChangeDutyCycle(0)
        pwm0_LB.ChangeDutyCycle(-speed)
        left_wheel_dirn = -1
    else:
        pwm1_LF.ChangeDutyCycle(0)
        pwm0_LB.ChangeDutyCycle(0)


def rotateRightWheel(speed):  # function to rotate right wheel
    global pwm2_RB, pwm3_RF, right_wheel_dirn
    if abs(speed) > 100:
        print('value of speed should be in between -100 and +100')
        return
    if speed > 0:
        pwm2_RB.ChangeDutyCycle(0)
        pwm3_RF.ChangeDutyCycle(speed)
        right_wheel_dirn = 1
    elif speed < 0:
        pwm3_RF.ChangeDutyCycle(0)
        pwm2_RB.ChangeDutyCycle(-speed)
        right_wheel_dirn = -1
    else:
        pwm3_RF.ChangeDutyCycle(0)
        pwm2_RB.ChangeDutyCycle(0)


def getDistanceCm():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)  # 10uS
    GPIO.output(TRIG, GPIO.LOW)

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = round(pulse_duration * 17150, 2)
    return distance


def us_func(_):
    global ultra_sonic_dist, path_client, lst_of_pts
    while not exit_threads:
        distances = []
        for i in range(0, 6):
            distances.append(getDistanceCm())
            time.sleep(0.02)
        distances.sort()
        # print(distances, ' --> ', distances[0], '||', distances[1])
        ultra_sonic_dist = (distances[0] + distances[1]) / 2
        if ultra_sonic_dist < 11:
            print('STOP Vehicle !!')
            lst_of_pts += str(6)
        elif ultra_sonic_dist < 17:
            print('Halt!!')
            lst_of_pts += str(7)
        else:
            print('follow path')
            lst_of_pts += str(8)

        # if path_client:
        #     if ultra_sonic_dist < 10:
        #         path_client.send('8'.encode())
        #     else:
        #         path_client.send('9'.encode())


def intVector(pin):  # function that reads inputs from encoders and act on change of input
    global increaser, left_ratio, left_holes, left_opaques, left_wheel_dirn, lrotations, right_holes, right_opaques, right_ratio, right_wheel_dirn, rrotations, lst_of_pts
    value1_temp = GPIO.input(18)
    value2_temp = GPIO.input(23)

    while True:
        value1 = GPIO.input(18)
        value2 = GPIO.input(23)
        if not value1 == value1_temp:  # if values have changed
            if value1:  # if input is high
                if left_wheel_dirn == 1:  # if direction is forward
                    left_opaques += 1  # increase opaque count
                else:
                    left_holes -= 1  # decrease holes count
            else:
                if left_wheel_dirn == 1:
                    left_holes += 1
                else:
                    left_opaques -= 1
            left_ratio += increaser * left_wheel_dirn  # ratio of wheel turn,, change according to direction of motion
            lst_of_pts += str(left_wheel_dirn + 3)  # encoder reading converted to string for sending to client socket
            # print('LEFT -->> holes, opaque  = ', left_holes, left_opaques)
            # print('L {0:0.3f}'.format(left_ratio))

            if abs(left_holes - left_opaques) > 1:  # count of holes and opaques should go simultaneously
                print('ERROR !!!!!! LEFT wheel encoder is not reading correctly')
            if left_holes == 20 and left_opaques == 20:  # one rotation contains 20 holes and 20 opaques counts
                lrotations += 1
                left_opaques = left_holes = 0
                print('LEFT one rotation completed !!!!!!', lrotations)
            elif left_holes == -20 and left_opaques == -20:  # similar but in reverse direction
                lrotations -= 1
                left_opaques = left_holes = 0
                print('LEFT one rotation in -VE direction completed !!!', lrotations)

        if not value2 == value2_temp:  # same as left but for right
            if value2:
                if right_wheel_dirn == 1:
                    right_opaques += 1
                else:
                    right_holes -= 1
            else:
                if right_wheel_dirn == 1:
                    right_holes += 1
                else:
                    right_opaques -= 1
            right_ratio += increaser * right_wheel_dirn
            lst_of_pts += str(2 * right_wheel_dirn + 3)
            # print('RIGHT -->> holes, opaque  =                  ', right_holes, right_opaques)
            # print('R {0:0.3f}'.format(right_ratio))

            if abs(right_holes - right_opaques) > 1:
                print('ERROR !!!!!! RIGHT wheel encoder is not reading correctly')

            if right_holes == 20 and right_opaques == 20:
                rrotations += 1
                right_holes = right_opaques = 0
                print('RIGHT one rotation completed !!!!!!', rrotations)
            elif right_holes == -20 and right_opaques == -20:
                rrotations -= 1
                right_holes = right_opaques = 0
                print('RIGHT one rotation in -VE direction completed !!!', rrotations)

        value2_temp = value2  # store previous value in order to check for change in value
        value1_temp = value1
        time.sleep(0.0001)  # to keep lower cpu load
    pass


def start_socket():  # starts socket at port=9818, in wifi ip address
    global serverSocket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    netifaces.ifaddresses('wlan0')
    ip = netifaces.ifaddresses('wlan0')[netifaces.AF_INET][0]['addr']
    host = str(ip)
    print('connect clients to', host)
    port = 9818
    serverSocket.bind((host, port))
    serverSocket.listen(21)
    return


def remote_client(client_, address_):  # client function for remote controller
    global lockKM, string_processor, exit_threads, gb_str, gb_valset, angle, speed
    lasttime = time.time()
    try:
        while True:
            msg = client_.recv(1024)  # receive bytes
            if not msg: break
            if len(msg) < 3: continue

            msg = msg.decode('utf-8')  # decoding byte to string(utf-8)
            inputs = msg.splitlines()  # split different lines
            print(inputs)
            for inp in inputs:
                if len(inp) < 3: continue
                variable, data = inp.split('=')  # split at every '=' sign (variable=data format is received)
                if variable == 'angle':
                    angle = float(data)
                elif variable == 'speed':
                    speed = float(data)
            # pinging
            if time.time() - lasttime > 30:  # pinging for connectivity purpose
                lasttime = time.time()
                msg = 'PSv: pinging' + "\r\n"
                client_.send(msg.encode())

    except OSError as e:  # if error occours,, close client
        print(e)
        print('closing client', address_)
        client_.close()
        pass
    finally:
        print('closing client', address_)
        client_.close()
    pass


def myTanHyp(val):  # input -1 to 1 output -100 to 100 in hyperbolic form
    val = math.tanh(val * 2)
    val = val / math.tanh(2)
    return val


def mySigmoid(x):  # sigmoid function
    return (200 / (1 + math.pow(math.e, -0.05 * x)) - 100) / 0.98662


def myLogit(x):
    return math.log(x / (1 - x))


def myLogarithmic(x):
    return 100 * math.log10(1 / (1 - 0.008 * x))


def driveMotors(_):  # drives motor according to angle of steering and speed/acceleration
    global speed, angle, exit_threads
    angle = speed = 0
    wheelLeft = wheelRight = 0
    tmpL = tmpR = 0
    while not exit_threads:
        time.sleep(0.01)
        # print('angle, speed = ',angle,speed)
        if angle >= 0:  # rotate right
            wheelLeft = speed / 4
            wheelRight = (1 - angle / 240) * wheelLeft  # minimum speed is half of left
            pass
        elif angle < 0:
            wheelRight = speed / 4
            wheelLeft = (1 + angle / 240) * wheelRight  # minimum speed is half of right
            pass

        if tmpL == wheelLeft and tmpR == wheelRight:  # if same speed as previous loop continue
            continue
        if speed == 0:
            wheelLeft = wheelRight = 0

        print('L R = ', wheelLeft, wheelRight)
        rotateRightWheel(wheelRight)  # rotate wheels
        rotateLeftWheel(wheelLeft)
        tmpL = wheelLeft  # to detect change in wheel speed
        tmpR = wheelRight
        # print('wheel l, r = ',wheelLeft, wheelRight)
    pass


def pathdrawer_client(client_, address_):  # handling path drawing client
    global lockKM, exit_threads, lst_of_pts, path_client, ultra_sonic_dist
    # path_client = client_
    lasttime = time.time()
    try:
        while True:
            msg = client_.recv(1024)
            if not msg: break
            if len(msg) < 3: continue

            # if ultra_sonic_dist < 10:
            #     lst_of_pts += str(8)
            # else:
            #     lst_of_pts += str(9)

            msg = msg.decode('utf-8').strip()  # remove unnecessary spaces
            if not msg == 'get_path':  # if not requested to get path
                print('pathdrawer msg = ', msg)
            if len(lst_of_pts) > 2:  # if list is not empty
                client_.send(lst_of_pts.encode())
            else:  # send null if list is empty
                client_.send('null'.encode())
            print(lst_of_pts)
            lst_of_pts = ''  # clear list of points

            # pinging
            if time.time() - lasttime > 30:
                lasttime = time.time()
                msg = 'PSv: pinging' + "\r\n"
                client_.send(msg.encode())

    except OSError as e:
        print(e)
        print('closing client', address_)
        client_.close()
        pass
    finally:
        print('closing client', address_)
        client_.close()
    pass


clientList = []  # all clients
addressList = []  # all addresses
threadList = []  # all threads
exit_threads = False  # to keep all threads running till this flag is TRUE

setup_gpio()
start_socket()

watcher = Thread(target=intVector, args=(0,), daemon=True)  # create thread to moniter the encoder inputs
watcher.start()
threadList.append(watcher)

driver = Thread(target=driveMotors, args=(0,), daemon=True)  # create threads to manage the motor rotations
driver.start()
threadList.append(driver)

us_thread = threading.Thread(target=us_func, args=(0,), daemon=True)
us_thread.start()
threadList.append(us_thread)
try:
    while True:
        time.sleep(1)
        client, address = serverSocket.accept()  # acccepting clients
        for addr in addressList:  # if address already exists as client reconnect and destroy previous client
            if address[0] == addr[0]:
                index = addressList.index(addr)
                print('same ip address again', addr[0])
                clientList[index].close()
                clientList.remove(clientList[index])
                addressList.remove(addressList[index])
                break
        print("Got a connection from %s" % str(address))  # successfully connected
        msg = 'PSv:Thank you for connecting' + "\r\n"
        client.send(msg.encode())  # thank you message

        msg = client.recv(1024)  # receive header for recognizing client type
        msg = msg.decode('utf-8').strip()
        print('msg= ', msg)
        if msg == 'android-remote':  # if it is android remote client
            print('Remote controller connected')
            mythread = threading.Thread(target=remote_client, args=(client, address,), daemon=True)
            mythread.start()  # start remote client thread
            clientList.append(client)
            addressList.append(address)
        elif msg == 'pc-pathdrawer':  # if it is pathdrawer
            print('Path drawer connected')
            mythread = threading.Thread(target=pathdrawer_client, args=(client, address,), daemon=True)
            mythread.start()  # start pathdrawer client handling thread
            clientList.append(client)
            addressList.append(address)

except KeyboardInterrupt:
    pass
finally:
    pwm0_LB.stop()
    pwm1_LF.stop()
    pwm2_RB.stop()
    pwm3_RF.stop()
    GPIO.cleanup()
    for c in clientList:
        try:
            c.close()
        except NameError as e:
            print(e)
            pass
    exit_threads = True
    serverSocket.close()
