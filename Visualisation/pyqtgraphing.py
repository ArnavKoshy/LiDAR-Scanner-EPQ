"""
This is my final code that I used with the scanner at my presentation
"""

from main import SerialReader
import sys
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.opengl as gl
from matplotlib import cm
import argparse

import traceback

class Visualizer(object):
    def __init__(self, queue):
        self.queue = queue
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts['distance'] = 40
        self.w.setWindowTitle('pyqtgraph example: GLLinePlotItem')
        self.w.setGeometry(0, 110, 1920, 1080)
        self.w.show()
        self.colors = np.empty((0,4), dtype=np.float32)
        self.colors = np.append(self.colors, [[1.0,1.0,1.0,1.0]], axis=0)
        self.xs, self.ys, self.zs = [0],[0],[0]
        self.scatter = pg.opengl.GLScatterPlotItem()
        a = np.array([self.xs, self.ys, self.zs])
        print(np.swapaxes(a,0,1).shape)
        self.scatter.setData(pos=np.swapaxes(a,0,1), color=(1.0,1.0,1.0,1.0), size=2.0)
        self.w.addItem(self.scatter)
        self.line = pg.opengl.GLLinePlotItem()
        self.w.addItem(self.line)
        self.map = cm.get_cmap('jet')




    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()



    def update(self):
        # Monitor Queue size
        print(self.queue.qsize(), end='\r')
        # Get (and remove) first item in queue
        if self.queue.empty():
            return
        datalist = self.queue.get()
        # print(datalist)
        try:
            a = np.deg2rad(datalist[0])
            b = np.deg2rad(datalist[1])
            dist = datalist[2]
            z = (np.sin(b) * dist)
            x = (np.cos(b) * np.cos(a) * dist)
            y = (np.cos(b)*np.sin(a)*dist)
            self.zs.append(z)
            self.ys.append(y)
            self.xs.append(x)
            a = np.array([self.xs, self.ys, self.zs])
            newcolor = np.clip(abs(dist)/2000, 0, 1)
            # print(dist)
            # print(newcolor)
            self.colors = np.append(self.colors, [list(self.map(1 - newcolor))], axis=0)
            # print(self.colors)
            # print(self.colors.shape)
            self.scatter.setData(pos=np.swapaxes(a,0,1), color=self.colors)
            self.line.setData(pos=np.array([[x,y,z], [0,0,0]]), color=(1.0,0.0,0.0,1.0), width=1.0)




        except Exception as e:
            print(e)
            print(datalist)


    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()

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

# Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':

    args = beginparser()
    # Initialise the queue where data will be stored
    dataqueue = queue.Queue()

    # Initialise SerialReader and set it to kill program if only it is left (when main thread dies)
    reader = SerialReader(args.port, args.baudrate, dataqueue)
    reader.daemon = True
    print("Starting Thread....")
    reader.start()

    v = Visualizer(dataqueue)
    v.animation()
