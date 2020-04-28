import os

from .feedback import Feedback
from qgis.core import Qgis, QgsTask, QgsMessageLog, QgsProcessingContext
import processing

from qgis.PyQt.QtCore import pyqtSignal

from .processing_provider.inference import InferenceQDeepLandiaProcessingAlgorithm


class InferenceTask(QgsTask):
    """This shows how to subclass QgsTask"""

    terminated = pyqtSignal(str)

    def __init__(self, description, iface, layer, nb_label, model_path, extent=None):
        super().__init__(description, QgsTask.CanCancel)
        self.feedback = Feedback(iface)
        self.param = { 'INPUT' : layer.id(), 'OUTPUT' : '/home/speillet/temp/tmp.tif', 'LABELS' : nb_label, 'MODEL' : model_path }
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
                name=self.description()), Qgis.Info)
        super().cancel()
