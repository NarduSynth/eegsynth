#!/usr/bin/env python

# This module provides a graphical interface with sliders and buttons
#
# This software is part of the EEGsynth project, see https://github.com/eegsynth/eegsynth
#
# Copyright (C) 2019 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import configparser
import argparse
import os
import redis
import sys
import time
import signal

if hasattr(sys, 'frozen'):
    basis = sys.executable
elif sys.argv[0] != '':
    basis = sys.argv[0]
else:
    basis = './'
installed_folder = os.path.split(basis)[0]

# eegsynth/lib contains shared modules
sys.path.insert(0,os.path.join(installed_folder, '../../lib'))
import EEGsynth

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inifile", default=os.path.join(installed_folder, os.path.splitext(os.path.basename(__file__))[0] + '.ini'), help="optional name of the configuration file")
args = parser.parse_args()

config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
config.read(args.inifile)

try:
    r = redis.StrictRedis(host=config.get('redis','hostname'), port=config.getint('redis','port'), db=0)
    response = r.client_list()
except redis.ConnectionError:
    print("Error: cannot connect to redis server")
    exit()

# combine the patching from the configuration file and Redis
patch = EEGsynth.patch(config, r)

# this determines how much debugging information gets printed
debug = patch.getint('general', 'debug')
prefix = patch.getstring('output', 'prefix')
output_scale  = patch.getfloat('output', 'scale', default=1./127)
output_offset = patch.getfloat('output', 'offset', default=0.)

slider  = []
button  = []

for item in config.items('slider'):
    slider.append(item[0])
for item in config.items('button'):
    button.append(item)

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50,50,500,300)
        self.setWindowTitle("inputcontrol")
        self.drawlayout()

    def drawlayout(self):
        mainlayout = QHBoxLayout()
        for item in slider:
            sliderlayout = QVBoxLayout()
            s = QSlider(Qt.Vertical)
            s.name = item
            s.type = 'slider'
            s.setMinimum(0)
            s.setMaximum(127)
            s.setValue(0)
            s.setTickInterval(1)
            s.setTickPosition(QSlider.TicksBelow)
            s.valueChanged.connect(self.changevalue)
            sliderlayout.addWidget(s)
            l = QLabel(item)
            l.setAlignment(Qt.AlignCenter)
            sliderlayout.addWidget(l)
            mainlayout.addLayout(sliderlayout)

        boxlayout = QVBoxLayout()
        for item in button:
            b = QPushButton(item[0])
            b.name = item[0]
            b.type = item[1]
            b.value = 0
            if item[1]=='slap':
                b.pressed.connect(self.changevalue) # push down
            else:
                b.clicked.connect(self.changevalue) # push down and release
            self.setcolor(b)
            boxlayout.addWidget(b)

        mainlayout.addLayout(boxlayout)
        self.setLayout(mainlayout)

    def changevalue(self):
        target = self.sender()

        if target.type=='slider':
            val = target.value()
        elif target.type=='slap':
            val = 127
        elif target.type=='push':
            val = 127
        elif target.type=='toggle1':
            target.value = (target.value + 1) % 2
            val = target.value * 127 / 1
        elif target.type=='toggle2':
            target.value = (target.value + 1) % 3
            val = target.value * 127 / 2
        elif target.type=='toggle3':
            target.value = (target.value + 1) % 4
            val = target.value * 127 / 3
        elif target.type=='toggle4':
            target.value = (target.value + 1) % 5
            val = target.value * 127 / 4
        self.setcolor(target)
        key = "%s.%s" % (prefix, target.name)
        val = EEGsynth.rescale(val, slope=output_scale, offset=output_offset)
        patch.setvalue(key, val, debug=debug)

    def setcolor(self, target):
        # see https://www.w3schools.com/css/css3_buttons.asp
        grey   = "background-color: rgb(250,250,250); border: 1px solid gray; border-radius: 4px; padding: 8px 4px;"
        red    = "background-color: rgb(255,0,0);     border: 1px solid gray; border-radius: 4px; padding: 8px 4px;"
        yellow = "background-color: rgb(250,250,60);  border: 1px solid gray; border-radius: 4px; padding: 8px 4px;"
        green  = "background-color: rgb(60,200,60);   border: 1px solid gray; border-radius: 4px; padding: 8px 4px;"
        amber  = "background-color: rgb(250,220,90);  border: 1px solid gray; border-radius: 4px; padding: 8px 4px;"

        if target.type=='toggle1':
            if target.value==1:
                target.setStyleSheet(red);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle2':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle3':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            elif target.value==3:
                target.setStyleSheet(green);
            else:
                target.setStyleSheet(grey);

        elif target.type=='toggle4':
            if target.value==1:
                target.setStyleSheet(red);
            elif target.value==2:
                target.setStyleSheet(yellow);
            elif target.value==3:
                target.setStyleSheet(green);
            elif target.value==4:
                target.setStyleSheet(amber);
            else:
                target.setStyleSheet(grey);

        elif target.type=='slap' or target.type=='push':
            target.setStyleSheet(grey);


def main():
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
