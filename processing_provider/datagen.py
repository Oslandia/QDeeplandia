# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import shutil
import subprocess

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber)
from qgis import processing



class DatagenQDeepLandiaProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    DATASET = 'DATASET'
    SHAPE = 'SHAPE'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DatagenQDeepLandiaProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DatagenQDeepLandia'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Datageneration')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('QDeepLandia')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'QDeepLandia'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Preprocess layer into predictable tiles")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Input layer')
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterString(
                self.DATASET,
                self.tr('Dataset name')
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SHAPE,
                self.tr('Number of pixel for the side of tiles'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 512,
                minValue = 16
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                self.tr('Output folder')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        raster_in = self.parameterAsRasterLayer(
            parameters,
            self.INPUT,
            context
        )

        dest_path = self.parameterAsString(
            parameters,
            self.OUTPUT,
            context
        )

        dataset = self.parameterAsString(
            parameters,
            self.DATASET,
            context
        )

        shape = self.parameterAsInt(
            parameters,
            self.SHAPE,
            context
        )

        path = ''
        for i in [dest_path, dataset, 'input', 'testing', 'images']:
            path = os.path.join(path, i)
            if not os.path.exists(path):
                os.mkdir(path)

        for file in os.listdir(path):
            os.remove(os.path.join(path,file))

        shutil.copy( raster_in.source(), os.path.join( path, os.path.basename( raster_in.source())))

        output_folder = os.path.join(dest_path, dataset, 'preprocessed', str(shape), 'testing', 'images')
        shutil.rmtree(os.path.join(dest_path, dataset, 'preprocessed', str(shape)))

        cmd = ['deepo', 'datagen', '-D', dataset, '-s', str(shape), '-P', dest_path, '-T', '1']
        subprocess.run(cmd)

        return {self.OUTPUT: output_folder}
