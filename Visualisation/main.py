"""
This is the matplotlib 3d code that ended up too slow for me to use on my laptop.
I modified the SerialReader class so it would work for my purposes and then used this in pyqtgraphing.py as well
"""

import threading
import sys
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.ticker as tkr
import argparse
import serial
from time import sleep
import os
import matplotlib.text as txt
import numpy as np


class SerialReader(threading.Thread):
    """Serial Reader class that provides an interface to read from a
        serial port and write to a queue on a separate threadself.
        Arguments: port{string} the port to connect to
                   baudrate{integer} the baudrate
                   q{queue.Queue object} the queue to write """

    def __init__(self, port, baudrate, q):
        super(SerialReader, self).__init__()
        self.q = q
        self.port = port
        self.baudrate = baudrate
        # Exceptions aren't thrown from threads to an interface has to be made to get the errors
        self.exception = None
        # Represent the last valid data point that was recieved
        self.lastdata = [0.0, 0.0]

    def run(self):
        # Try to open the serial port
        print("Opening Serial Port....")
        try:
            self.conn = serial.Serial(port=self.port, baudrate=self.baudrate)
            print("Reading from port %s..." % self.port)
        # Exit all threads if could not connect
        except Exception as e:
            print(
                "Error when opening port. Check Spellings and if there is a device plugged in")
            self.exception = e
            print(self.exception)
            os._exit(1)
        self.conn.flush()
        self.conn.reset_input_buffer()

        # Forever
        while True:
            sleep(0.01)
            bytes = self.conn.readline()
            try:
                # Format the data to a list of floats
                data = [float(val) for val in bytes.decode("ascii").strip().split(',')]
                self.lastdata = data
            except Exception as e:
                print("There was an issue converting:", bytes)
                self.exception = e
            # Write to queue
            self.q.put(self.lastdata)
            # Monitor serial buffer
            if self.conn.in_waiting > 100:
                print("!!!Danger, Higher than average serial buffer. You will experience lag %i" %
                      self.conn.in_waiting)

    def get_exception(self):
        return self.exception


class Plotter(object):
    """Plotter class that encapsulates all the necessary methods to make pyplots easy to use
        Args: Queue object that represents incoming data queue
              maxLength: Length of x-axis and data
    """

    def __init__(self, queue, maxLength):
        super(Plotter, self).__init__()
        self.Paused = False
        self.maxLength = maxLength
        self.queue = queue
        #  set up the graph and axes and do a bunch of formatting
        self.fig = plt.figure()
        self.axes = self.fig.add_subplot(111, projection='3d')
        # self.axes = plt.axes(xlim=(0, self.maxLength), ylim=(0,3.3))
        # self.axes.yaxis.tick_right()
        # self.axes.yaxis.set_major_locator(tkr.LinearLocator(numticks=9))
        # self.axes.yaxis.set_minor_locator(tkr.AutoMinorLocator(n=5))
        self.xs, self.ys, self.zs = [], [], []
        self.scatter, = self.axes.plot(self.xs, self.ys,self.zs, linestyle="")
        self.cid = self.fig.canvas.mpl_connect('key_press_event', self.OnSpace)

    # This function updates the graph every time FuncAnimation calls it
    def update(self, i):
        if self.Paused:
            return
        # Monitor Queue size
        print(self.queue.qsize())
        # Get (and remove) first item in queue
        datalist = self.queue.get()
        print(datalist)
        try:
            a = np.deg2rad(datalist[0])
            b = np.deg2rad(datalist[1])
            dist = np.deg2rad(datalist[2])
            z = (np.sin(b) * dist)
            x = (np.cos(b) * np.cos(a) * dist)
            y = (np.cos(b)*np.sin(a)*dist)
            self.zs.append(z)
            self.ys.append(y)
            self.xs.append(x)
            point, = self.axes.plot(self.xs, self.ys, self.zs, markerfacecolor='b', marker='o', markersize=2, linestyle="")
            # self.scatter.set_3d_properties(self.z)
            minimax = [np.amin(self.xs + self.ys + self.zs), np.amax(self.xs + self.ys + self.zs)]
            self.axes.set_xlim(minimax)
            self.axes.set_ylim(minimax)
            self.axes.set_zlim(minimax)
            # print(type(point[0]))
            return self.axes, point



        except Exception as e:
            print(str(e))
            return self.scatter,


    # Function that is called on spacebar pressed
    def OnSpace(self, event):
        if event.key == ' ':
            self.Paused = not self.Paused
            if not self.Paused:
                with self.queue.mutex:
                    self.queue.queue.clear()


def beginparser():
    """
    Makes a new instance of ArgumentParser and then adds the required command line Arguments
    Return type dictionary of arguments
    """
    parser = argparse.ArgumentParser(description="SerialPlotter")
    parser.add_argument('--port', dest='port', required=True)
    parser.add_argument('--baud', dest='baudrate', required=True, type=int)
    parser.add_argument('--len', dest='maxLength', default=100, type=int)
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = beginparser()

    # Initialise the queue where data will be stored
    dataqueue = queue.Queue()

    # Initialise SerialReader and set it to kill program if only it is left (when main thread dies)
    reader = SerialReader(args.port, args.baudrate, dataqueue)
    reader.daemon = True
    print("Starting Thread....")
    reader.start()

    # Initialise plotter class
    plot = Plotter(dataqueue, args.maxLength)

    # define the animation to run (calls plot.update every 1 ms with blitting)
    anim = animation.FuncAnimation(plot.fig, plot.update, interval=1, blit=True)

    print("Initialised plot")

    # start the actual plot
    plt.show()

    print("exiting")

    # clear up all the io buffers and close port
    reader.conn.flush()
    reader.conn.reset_input_buffer()
    reader.conn.close()
