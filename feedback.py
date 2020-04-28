from qgis.core import Qgis, QgsProcessingFeedback, QgsMessageLog

class Feedback(QgsProcessingFeedback):
    """To provide feedback to the message bar from the express tools"""

    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.fatal_errors = []

    def reportError(self, error, fatalError=False):
        QgsMessageLog.logMessage(str(error), "QDeeplandia")
        if fatalError:
            self.fatal_errors.append(error)

    def pushToUser(self, exception):
        QgsMessageLog.logMessage(str(exception), "QDeeplandia")
        self.iface.messageBar().pushMessage(
            "Error", ", ".join(self.fatal_errors), level=Qgis.Critical, duration=0
        )