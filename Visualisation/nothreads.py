"""
This is the 2d program I wrote to test the sensor and my working principle
"""

import serial
import matplotlib.pyplot as plt
import time
import numpy as np
import matplotlib.animation as animation

ser = serial.Serial('/dev/ttyUSB0', 115200)
fig, axes = plt.subplots()
xs, ys = [], []
plt.xlim(-50,500)
plt.ylim(0,100)
scatter = axes.scatter(xs, ys)


def animate(i):
    data = ser.readline()
    if(not data):
        return
    datalist = []
    try:
        datalist = [float(val) for val in data.decode("ascii").strip().split(',')]
    except Exception as e:
        print(e)
        return
    try:
        xs.append(np.sin(datalist[0]) * datalist[2])
        ys.append(np.cos(datalist[0]) * datalist[2])
        scatter.set_offsets(np.c_[xs,ys])
    except Exception as e:
        print(str(e))
        return

anim = animation.FuncAnimation(fig, animate, interval=10, repeat=True)
plt.show()
