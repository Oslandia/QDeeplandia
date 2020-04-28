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

from qgis.core import Qgis, QgsRasterDataProvider, QgsApplication, \
                      QgsProcessingFeedback, QgsMessageLog, QgsProcessingContext

import processing

from qgis.PyQt.QtCore import QSettings, QCoreApplication, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QWidget, \
                                QHBoxLayout, QVBoxLayout, QMessageBox, \
                                QToolBar, QLabel, QCheckBox

os.environ['DEEPOSL_CONFIG']=os.path.join(os.path.dirname(__file__),'config.ini')
from .deeposlandia import postprocess
from .processing_provider.provider import QDeepLandiaProvider

from .gui.NbLabelDialog import NbLabelDialog

from .inferenceTask import InferenceTask

def tr(message):
    """Get the translation for a string using Qt translation API.
    """
    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    return QCoreApplication.translate('@default', message)

class QDeeplandiaPlugin(QWidget):
    """ Major class of QDeeplandia plugin """

    isready = pyqtSignal()

    def __init__(self, iface):
        """Constructor

        :param iface: qgis interface
        :type iface:QgisInterface
        """
        super(QDeeplandiaPlugin, self).__init__()
        self.iface = iface
        self.mapCanvas = self.iface.mapCanvas()
        self.model = None
        self.deepOprovider = None
        self.layer = self.updateLayer()
        self.nb_labels = None
        self.model_path = None
        self.datapath = None
        self.dataset = None

        locale = QSettings().value('locale/userLocale') or 'en_USA'
        locale= locale[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__),
            'i18n',
            'thyrsis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path, 'qdeeplandia')
            QCoreApplication.installTranslator(self.translator)
            print("TRANSLATION LOADED", locale_path)

        self.mapCanvas.currentLayerChanged.connect(self.updateLayer)
        self.isready.connect(self.ready)

    def initGui(self):
        # Select a trained model on the file system
        self.initProcessing()

        self.toolbar = QToolBar("QDeepLandia_toolbar")
        self.toolbar.setObjectName("QDeepLandia_toolbar")
        # self.toolbar.setMaximumWidth(180)
        self.toolbar.addWidget(QLabel("QDeeplandia"))
        self.iface.addToolBar(self.toolbar)

        # Load model process
        load_model_msg = tr("Load a trained model")
        load_icon = QIcon(os.path.join(os.path.dirname(__file__), "img/load.svg"))
        self.model_loading = QAction(load_icon, load_model_msg, self.iface.mainWindow())
        self.model_loading.triggered.connect(lambda: self.load_trained_model())
        self.iface.addPluginToMenu("QDeeplandia", self.model_loading)
        self.toolbar.addAction(self.model_loading)

        # Run-an-inference process
        run_inference_msg = tr("Run an inference")
        run_icon = QIcon(os.path.join(os.path.dirname(__file__), "img/run.svg"))
        self.inference = QAction(run_icon, run_inference_msg, self.iface.mainWindow())
        self.inference.triggered.connect(lambda: self.infer())
        self.iface.addPluginToMenu("QDeeplandia", self.inference)
        self.toolbar.addAction(self.inference)
        self.inference.setEnabled(False)

        # Use canvas parameters
        self.canvasCheckbox = QCheckBox('Use canvas extent')
        self.toolbar.addWidget(self.canvasCheckbox)

    def initProcessing(self):
        self.deepOprovider = QDeepLandiaProvider()
        QgsApplication.processingRegistry().addProvider(self.deepOprovider)

    def unload(self):
        # Select a trained model on the file system
        self.iface.removePluginMenu("QDeeplandia", self.model_loading)
        self.toolbar.setParent(None)
        self.model_loading.setParent(None)
        # Run-an-inference process
        self.iface.removePluginMenu("QDeeplandia", self.inference)
        self.inference.setParent(None)
        QgsApplication.processingRegistry().removeProvider(self.deepOprovider)

    def tr(message):
        """Get the translation for a string using Qt translation API.
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('@default', message)

    def load_trained_model(self):
        self.model_path, __ = QFileDialog.getOpenFileName(None,
                tr("Load best-model-*.h5 file"),
                os.path.abspath("."),
                tr("h5 file (*.h5)"))

        if not self.model_path :
            return

        nbLabelDlg = NbLabelDialog(self)

        if nbLabelDlg.exec():
            self.nb_labels = nbLabelDlg.param()
        else :
            return
        
        self.datapath = os.path.abspath(os.path.join(os.path.dirname(self.model_path), '..', '..', '..', '..'))
        self.dataset = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(self.model_path), '..', '..', '..')))
        self.image_size = os.path.splitext(os.path.basename(self.model_path))[0].split('-')[-1]
        try :
            self.model = postprocess.get_trained_model(self.datapath, self.dataset, int(self.image_size), int(self.nb_labels))
        except ValueError as e:
            self.iface.messageBar().pushMessage(tr("Critical"),
                    str(e), level=Qgis.Critical)

        if self.model :
            self.updateLayer()

    def infer(self):
        extent = None
        if self.canvasCheckbox.checkState() :
            extent = self.mapCanvas.extent()

        def addOutput(layer):
            self.iface.addRasterLayer(layer)

        task = InferenceTask('Inference', self.iface, self.layer, self.nb_labels, self.model_path, extent)
        task.terminated.connect(addOutput)
        QgsApplication.taskManager().addTask(task)

    def updateLayer(self):
        layer = self.mapCanvas.currentLayer()
        if layer :
            if isinstance(layer.dataProvider(), QgsRasterDataProvider):
                self.layer = layer
            else :
                self.layer = None
        else : 
            self.layer = None
        self.isready.emit()

    def ready(self) :
        if self.layer and self.model :
            self.inference.setEnabled(True)