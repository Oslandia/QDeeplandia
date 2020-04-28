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
import sys
import glob
import gdal
import shutil
import numpy as np

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsRasterLayer,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterExtent)
from qgis import processing

from deeposlandia.inference import predict
from deeposlandia.postprocess import get_trained_model, extract_images, \
                                     extract_coordinates_from_filenames, \
                                     build_full_labelled_image, get_labels, \
                                     assign_label_colors, draw_grid

class InferenceQDeepLandiaProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    EXTENT = 'EXTENT'
    MODEL = 'MODEL'
    LABELS = 'LABELS'
    OUTPUT = 'OUTPUT'

    def __init__(self, model=None):
        super().__init__()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return InferenceQDeepLandiaProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'InferenceQDeepLandia'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Inference')

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
        return self.tr("Do inference according to the loaded model")

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

        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('Input extent'),
                defaultValue= None,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.MODEL,
                self.tr('Input model'),
                extension="h5"
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.LABELS,
                self.tr('Number of labels used for the inference'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 4,
                minValue = 2,
                optional = True
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output file')
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

        output_path = self.parameterAsString(
            parameters,
            self.OUTPUT,
            context
        )

        model_path = self.parameterAsString(
            parameters,
            self.MODEL,
            context
        )
        nb_labels = self.parameterAsInt(
            parameters,
            self.LABELS,
            context
        )

        datapath = os.path.abspath(os.path.join(os.path.dirname(model_path), '..', '..', '..', '..'))
        dataset = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(model_path), '..', '..', '..')))
        image_size = os.path.splitext(os.path.basename(model_path))[0].split('-')[-1]
        try :
            model = get_trained_model(datapath, dataset, int(image_size), int(nb_labels))
        except:
            sys.exit()

        extent = self.parameterAsExtent(
            parameters,
            self.EXTENT,
            context
        )

        param = { 'INPUT': raster_in.id(), 'OUTPUT': datapath, 'DATASET': dataset, 'SHAPE': image_size}
        if extent.xMinimum() != 0 and extent.xMaximum() != 0:
            if ((extent.xMaximum() - extent.xMinimum())/raster_in.rasterUnitsPerPixelX() >= int(image_size) and \
               (extent.yMaximum() - extent.yMinimum())/raster_in.rasterUnitsPerPixelY() >= int(image_size)):
                clipped = os.path.join(os.path.dirname(output_path), 'clipped.tif')
                param = { 'INPUT': raster_in.id(), 'PROJWIN': extent, 'OUTPUT': clipped}
                out = processing.run('gdal:cliprasterbyextent', param, feedback=feedback)
                param = { 'INPUT': out['OUTPUT'], 'OUTPUT': datapath, 'DATASET': dataset, 'SHAPE': image_size}
                raster_in = QgsRasterLayer(out['OUTPUT'],'clipped', 'gdal')
        
        out = processing.run('QDeepLandia:DatagenQDeepLandia', param, feedback=feedback)

        raster_list = glob.glob(os.path.join(out['OUTPUT'],'*.png'))
        images = extract_images(raster_list)
        coordinates = extract_coordinates_from_filenames(raster_list)
        labels = get_labels(datapath, dataset, image_size)

        data = build_full_labelled_image(
            images,
            coordinates,
            model,
            int(image_size),
            int(raster_in.width()),
            int(raster_in.height()),
            128
        )

        colored_data = assign_label_colors(data, labels)
        colored_data = draw_grid(
            colored_data, int(raster_in.width()), int(raster_in.height()), int(image_size)
        )
        predicted_label_folder = os.path.join(
            datapath,
            dataset,
            "output",
            "semseg",
            "predicted_labels"
        )
        os.makedirs(predicted_label_folder, exist_ok=True)
        predicted_label_file = os.path.join(
            predicted_label_folder,
            os.path.basename(os.path.splitext(raster_in.source())[0]) + "_" + str(image_size) + ".tif",
        )
        ds = gdal.Open(raster_in.source())
        CreateGeoTiff(predicted_label_file, colored_data, ds.GetGeoTransform(), ds.GetProjection())
        shutil.copy(predicted_label_file, output_path)
        return {self.OUTPUT: output_path}

def CreateGeoTiff(outRaster, data, geo_transform, projection):
    driver = gdal.GetDriverByName('GTiff')
    rows, cols, no_bands = data.shape
    DataSet = driver.Create(outRaster, cols, rows, no_bands, gdal.GDT_Byte)
    DataSet.SetGeoTransform(geo_transform)
    DataSet.SetProjection(projection)

    data = np.moveaxis(data, -1, 0)

    for i, image in enumerate(data, 1):
        DataSet.GetRasterBand(i).WriteArray(image)
    DataSet = None