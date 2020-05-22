import os
import sys

from .feedback import Feedback
from qgis.core import Qgis, QgsTask, QgsMessageLog, QgsProcessingContext
import processing
import random, string

from qgis.PyQt.QtCore import pyqtSignal

from .processing_provider.inference import InferenceQDeepLandiaProcessingAlgorithm


class InferenceTask(QgsTask):
    """InferenceTask is a QgsTask subclass"""

    terminated = pyqtSignal(str)

    def __init__(self, description, iface, layer, nb_label, model_path, extent=None):
        super().__init__(description, QgsTask.CanCancel)
        self.feedback = Feedback(iface)
        if sys.platform == 'windows' :
            tmp_folder = os.path.join(os.environ['LOCALAPPDATA'], 'QGIS')
        else :
            tmp_folder = '/tmp'
        tmp_name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)) + '.tif'
        self.param = { 'INPUT' : layer.id(), 'OUTPUT' : os.path.join(tmp_folder,tmp_name), 'LABELS' : nb_label, 'MODEL' : model_path }
        if extent :
            self.param['EXTENT'] = extent

    def run(self):
        out = processing.run('QDeepLandia:InferenceQDeepLandia', self.param, feedback=self.feedback)
        if os.path.exists(out['OUTPUT']):
            self.terminated.emit(out['OUTPUT'])
        return True

    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=self.description()), "QDeeplandia")
        self.terminated.emit(None)
        super().cancel()
