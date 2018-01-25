import socket
import time
import math
import matplotlib.pyplot as plt
from matplotlib.path import Path
import threading
import numpy as np

exit_threads = False
lists = []
maxl = maxr = minr = minl = 0  # max values for ploting graph
perimeter = 6.5 * math.pi
one_unit = perimeter / 40  # when one hole or opaque is travelled
half_unit = one_unit / 2
dist = 13.5  # distance between left and right wheels
half_dist = dist / 2  # distance to middle
one_ang = math.pi / 2 / 40  # angle when one hole or opaque is travelled

lwx, lwy = 0, dist / 2  # initially left wheel (x,y)
rwx, rwy = 0, -dist / 2  # initially right wheel (x,y)
middlex, middley = 0, 0  # initially mid at origin
angle = 0  # angle of the vehicle turning

leftWheelX = []  # wheel positions for plotting
leftWheelY = []
rightWheelX = []
rightWheelY = []
middleWheelX = []
middleWheelY = []

m = 0  # for equation  y = mx + c
c = 0


def receiverThread(jpt):  # receives path form server
    global server, exit_threads, lists, maxr, minr, maxl, minl, l, r, angle, lwx, lwy, rwx, rwy, m, c
    global middlex, middley, one_unit, one_ang, leftWheelX, leftWheelY, rightWheelX, rightWheelY, middleWheelX, middleWheelY, half_unit
    while not exit_threads:

        msg = server.recv(1024)
        msg = msg.decode('utf-8').strip()
        print('message = ', msg)
        if msg == 'null':
            continue
        if msg[:3] == 'PSv':
            continue
        for character in msg:
            item = int(character) - 5  # convert string to integer and back to original
            ldx = rdx = ldy = rdy = 0  # change in distance according to input
            if item == 1:  # left wheel forward
                angle -= one_ang  # turns clockwise hence angle decreases
                ldx = math.cos(angle)
                ldy = math.sin(angle)
                pass
            elif item == -1:  # left wheel backward
                angle += one_ang  # turns anticlockwise
                ldx = -math.cos(angle)
                ldy = -math.sin(angle)
                pass
            elif item == 2:  # right wheel forward
                angle += one_ang  # turns anticlockwise
                rdx = math.cos(angle)
                rdy = math.sin(angle)
                pass
            else:  # right wheel backward
                angle -= one_ang  # turns clockwise
                rdx = -math.cos(angle)
                rdy = -math.sin(angle)
                pass

            # any unit of movement in left or right moves middle only half
            middlex, middley = middlex + (ldx + rdx) * half_unit, middley + (ldy + rdy) * half_unit
            middleWheelX.append(middlex)
            middleWheelY.append(middley)

            # lwx, lwy = lwx + ldx * one_unit, lwy + ldy * one_unit
            # rwx, rwy = rwx + rdx * one_unit, rwy + rdy * one_unit

            a = math.sin(math.pi / 2 + angle) * half_dist  # corresponding x axis motion according to angle of car
            b = math.cos(math.pi / 2 + angle) * half_dist  # corresponding y axis motion according to angle of car
            lwx = middlex + b  # calculate new position of wheels
            lwy = middley + a
            rwx = middlex - b
            rwy = middley - a

            # m = math.tan(angle + math.pi/2)
            # pmval = half_dist / math.sqrt(1 + m * m)
            # lwx = pmval + middlex
            # rwx = -pmval + middlex
            # c = middley - m * middlex
            # lwy = m * lwx + c
            # rwy = m * lwx + c
            # print('slope=',m, 'angle=',angle+math.pi/2)

            # if m <= 1:
            #     x = np.arange(lwx, rwx, 0.05)
            #     y = x * m + c
            #     print(x)
            #     print(y)
            #     leftWheelX = np.append(leftWheelX, x)
            #     leftWheelY = np.append(leftWheelY, y)
            # else:
            #     y = np.arange(lwy, rwy, 0.05)
            #     x = (y - c) / m
            #     print(x)
            #     print(y)
            #     leftWheelX = np.append(leftWheelX, x)
            #     leftWheelY = np.append(leftWheelY, y)
            #
            # print(leftWheelX)
            # print(leftWheelY)

            leftWheelX.append(lwx)
            leftWheelY.append(lwy)
            rightWheelX.append(rwx)
            rightWheelY.append(rwy)

            print('ldx, ldy = ', ldx, ldy)
            print('mid = ', middlex, middley)

            distance = math.sqrt(math.pow(lwx - rwx, 2) + math.pow(lwy - rwy, 2))  # checking distance for accuracy
            # if not distance == dist:
            #     diff = dist - distance
            #     annn = (angle + math.pi)
            #     lwy += math.sin(annn) * diff / 2
            #     lwx += math.cos(annn) * diff / 2
            #     rwy -= math.sin(annn) * diff / 2
            #     rwx -= math.cos(annn) * diff / 2

            print('left = ', lwx, lwy, '  right = ', rwx, rwy, ' angle = ', angle)
            print('distance = ', distance)


try:
    server = socket.socket()
    host = '192.168.0.50'
    port = 9818
    server.connect((host, port))  # connect to raspi
    print("Connected to IP - " + host)
    time.sleep(1)
    server.send('pc-pathdrawer'.encode())  # indicate it as path drawer

    msg = server.recv(1024)
    msg = msg.decode('utf-8')
    print('message from server = ', msg)

    mythread = threading.Thread(target=receiverThread, args=(0,), daemon=True)  # start listening to server
    mythread.start()

    plt.ion()  # for continuous plot
    fig = plt.figure()
    ax = fig.add_subplot(111)
    length_data = 0

    while True:
        time.sleep(1)
        server.send('get_path'.encode())  # sending request to path data

        if len(middleWheelY) < 3: continue  # start plotting after some data is received
        if len(middleWheelY) == length_data: continue
        length_data = len(leftWheelY)

        # calculate max and min for graph scaling purpose
        maxx = max([max(leftWheelX), max(rightWheelX)])
        minx = min([min(leftWheelX), min(rightWheelX)])
        maxy = max([max(leftWheelY), max(rightWheelY)])
        miny = min([min(leftWheelY), min(rightWheelY)])

        # set graph limit on axis
        ax.set_xlim(minx * 1.1 - 1, maxx * 1.1 + 1)
        ax.set_ylim(miny * 1.1 - 1, maxy * 1.1 + 1)
        line1, line2, line3 = ax.plot(leftWheelX, leftWheelY, 'r--', rightWheelX, rightWheelY, 'g--', middleWheelX,
                                      middleWheelY, 'b-')  # define 3 lines for left right and mid
        fig.canvas.draw()

except KeyboardInterrupt:
    pass
finally:
    exit_threads = True
    server.close()
