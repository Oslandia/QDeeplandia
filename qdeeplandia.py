# -*- coding: utf-8 -*-
#
#   Copyright (C) 2020 Oslandia <infos@oslandia.com>
#
#   This file is a piece of free software; you can redistribute it and/or
#   modify it under the terms of the GNU Library General Public
#   License as published by the Free Software Foundation; either
#   version 2 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Library General Public License for more details.
#   You should have received a copy of the GNU Library General Public
#   License along with this library; if not, see <http://www.gnu.org/licenses/>.
#

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class QDeeplandiaPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # Select a trained model on the file system
        self.load_model_action = QAction(
            "Select a trained model", self.iface.mainWindow()
        )
        self.load_model_action.triggered.connect(self.load_trained_model)
        self.iface.addPluginToMenu("QDeeplandia", self.load_model_action)
        # Run icon
        icon = QIcon(os.path.join(os.path.dirname(__file__), "img/run.svg"))
        self.inference = QAction(icon, u'Run inference', self.iface.mainWindow())
        self.inference.triggered.connect(lambda: self.infer())
        self.iface.addToolBarIcon(self.inference)

    def unload(self):
        # Remove the plugin menu
        self.iface.removePluginMenu("QDeeplandia", self.load_model_action)
        self.load_model_action.setParent(None)
        # Remove the icon from the tool bar
        self.iface.removeToolBarIcon(self.inference)
        self.inference.setParent(None)

    def load_trained_model(self):
        pass

    def infer(self):
        pass
