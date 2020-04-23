from qgis.PyQt.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox

class NbLabelDialog(QDialog):
    def __init__(self,parent):
        super(NbLabelDialog, self).__init__()

        self.VL = QVBoxLayout(self)
        self.HL = QHBoxLayout()
        self.VL.addLayout(self.HL)

        self.label = QLabel(self.tr('Number of label : '))
        self.HL.addWidget(self.label)

        self.spinbox = QSpinBox()
        self.HL.addWidget(self.spinbox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.VL.addWidget(self.buttonBox)

    def param(self):
        return self.spinbox.value()