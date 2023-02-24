"""
Model exported as python.
Name : 1.Carregar Fotos
Group : Óleo
With QGIS : 32216
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class CarregarFotos(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile('pastacomasfotos', 'Pasta com as fotos', behavior=QgsProcessingParameterFile.Folder, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Fotos', 'Fotos', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('FotosSemCoordenadas', 'Fotos sem coordenadas', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Import geotagged photos
        alg_params = {
            'FOLDER': parameters['pastacomasfotos'],
            'RECURSIVE': True,
            'INVALID': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ImportGeotaggedPhotos'] = processing.run('native:importphotos', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Cria SubmissionID
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'submid',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'right("directory",19)',
            'INPUT': outputs['ImportGeotaggedPhotos']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriaSubmissionid'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # submid para fotos sem coordenadas
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'submid',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'right("directory",19)',
            'INPUT': outputs['ImportGeotaggedPhotos']['INVALID'],
            'NEW_FIELD': True,
            'OUTPUT': parameters['FotosSemCoordenadas']
        }
        outputs['SubmidParaFotosSemCoordenadas'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['FotosSemCoordenadas'] = outputs['SubmidParaFotosSemCoordenadas']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Cria x
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'x',
            'FIELD_PRECISION': 6,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '"longitude"',
            'INPUT': outputs['CriaSubmissionid']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriaX'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # cria Y
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'y',
            'FIELD_PRECISION': 6,
            'FIELD_TYPE': 0,  # Float
            'FORMULA': '"latitude"',
            'INPUT': outputs['CriaX']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': parameters['Fotos']
        }
        outputs['CriaY'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Fotos'] = outputs['CriaY']['OUTPUT']
        return results

    def name(self):
        return '1.Carregar Fotos'

    def displayName(self):
        return '1.Carregar Fotos'

    def group(self):
        return 'Óleo'

    def groupId(self):
        return 'Óleo'

    def createInstance(self):
        return CarregarFotos()
