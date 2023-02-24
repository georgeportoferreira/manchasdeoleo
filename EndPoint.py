"""
Model exported as python.
Name : Endpoint
Group : Óleo
With QGIS : 32216
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Endpoint(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('jotformlegado', 'JotForm Legado', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('localidadea', 'localidade_a', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('olhosdeguia20nov2019atopresente', 'Olhos de Águia (20/nov/2019 até o presente)', types=[QgsProcessing.TypeVector], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Endponint', 'EndPonint', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(17, model_feedback)
        results = {}
        outputs = {}

        # identifica loc_id mais proximo
        alg_params = {
            'FIELD': 'loc_id',
            'HUBS': parameters['localidadea'],
            'INPUT': parameters['olhosdeguia20nov2019atopresente'],
            'UNIT': 0,  # Meters
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IdentificaLoc_idMaisProximo'] = processing.run('qgis:distancetonearesthubpoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # todos registros
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['IdentificaLoc_idMaisProximo']['OUTPUT'],parameters['jotformlegado']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TodosRegistros'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # popula loc_id
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'loc_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'if (loc_id is null, HubName, loc_id)',
            'INPUT': outputs['TodosRegistros']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PopulaLoc_id'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Popula campo data
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'date',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 3,  # Date
            'FORMULA': 'to_date(concat(right("Data",4),\'-\',substr("Data",4,2),\'-\',left("Data",2)))',
            'INPUT': outputs['PopulaLoc_id']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PopulaCampoData'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Popula range com oleo
        alg_params = {
            'FIELD_LENGTH': 25,
            'FIELD_NAME': 'rangeOL',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat( to_date(minimum("date", loc_id, status !=   \'Oleo Nao Observado\' )), \', \',to_date(maximum("date", loc_id, status !=   \'Oleo Nao Observado\' )))',
            'INPUT': outputs['PopulaCampoData']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PopulaRangeComOleo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Popula range sem oleo
        alg_params = {
            'FIELD_LENGTH': 25,
            'FIELD_NAME': 'rangeNO',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat( to_date(minimum("date", loc_id, status =   \'Oleo Nao Observado\' )), \', \',to_date(maximum("date", loc_id, status =   \'Oleo Nao Observado\' )))',
            'INPUT': outputs['PopulaRangeComOleo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PopulaRangeSemOleo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # idparaDissolver
        alg_params = {
            'FIELD_LENGTH': 60,
            'FIELD_NAME': 'dissolvido',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat("date",status,loc_id)',
            'INPUT': outputs['PopulaRangeSemOleo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Idparadissolver'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Dissolvido
        alg_params = {
            'FIELD': 'dissolvido',
            'INPUT': outputs['Idparadissolver']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolvido'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # cria campo qtd_vistorias
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'qtd_vistorias',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': "count($id, loc_id, (status = 'Oleo Nao Observado'))",
            'INPUT': outputs['Dissolvido']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriaCampoQtd_vistorias'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # data intercala
        alg_params = {
            'FIELD_LENGTH': 25,
            'FIELD_NAME': 'intercala',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': "CASE \r\n  WHEN  left(rangeNO,10)<right(rangeOL,10) and right(rangeNO,10)>right(rangeOL,10) THEN concat(right(rangeOL,10),', ',right(rangeNO,10))\r\n  WHEN  left(rangeNO,10)>=right(rangeOL,10) THEN 'OK'\r\n  ELSE 'fora'\r\nEND",
            'INPUT': outputs['CriaCampoQtd_vistorias']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DataIntercala'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Popula novo range
        alg_params = {
            'FIELD_LENGTH': 25,
            'FIELD_NAME': 'rangeNO',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': "CASE \r\n  WHEN  intercala = 'OK' THEN rangeNO\r\n  WHEN  intercala not in ('OK','fora') THEN intercala\r\n  ELSE null END",
            'INPUT': outputs['DataIntercala']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PopulaNovoRange'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # qtd vistorias sem oleo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'qtd_vistorias',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'if (intercala is not null, count($id, loc_id, (status = \'Oleo Nao Observado\' and "date">to_date(left(intercala,10)))),qtd_vistorias)',
            'INPUT': outputs['PopulaNovoRange']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['QtdVistoriasSemOleo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Dissolve por loc_id
        alg_params = {
            'FIELD': 'loc_id',
            'INPUT': outputs['QtdVistoriasSemOleo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DissolvePorLoc_id'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Dias sem oleo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'diassemoleo',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer
            'FORMULA': 'day(to_interval(to_date(right(rangeNO,10)) - to_date(left(rangeNO,10))))',
            'INPUT': outputs['DissolvePorLoc_id']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DiasSemOleo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # seleciona reg de interesse
        alg_params = {
            'EXPRESSION': "rangeOL != ', ' and qtd_vistorias >2",
            'INPUT': outputs['DiasSemOleo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SelecionaRegDeInteresse'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Join attributes by field value
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELD': 'loc_id',
            'FIELDS_TO_COPY': None,
            'FIELD_2': 'loc_id',
            'INPUT': outputs['SelecionaRegDeInteresse']['OUTPUT'],
            'INPUT_2': parameters['localidadea'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': 'l',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByFieldValue'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"llocalidade"','length': 0,'name': 'nome_localidade','precision': 0,'type': 10},{'expression': '"lmunicipio"','length': 0,'name': 'municipio','precision': 0,'type': 10},{'expression': '"lsigla_uf"','length': 254,'name': 'Estado','precision': 0,'type': 10},{'expression': '$x','length': 10,'name': 'x','precision': 6,'type': 6},{'expression': '$y','length': 10,'name': 'y','precision': 6,'type': 6},{'expression': '"loc_id"','length': 12,'name': 'loc_id','precision': 0,'type': 10},{'expression': '"rangeOL"','length': 25,'name': 'intervalocomoleo','precision': 3,'type': 10},{'expression': '"rangeNO"','length': 25,'name': 'intervalosemoleo','precision': 3,'type': 10},{'expression': '"qtd_vistorias"','length': 10,'name': 'qtd_vistorias','precision': 3,'type': 2},{'expression': '"diassemoleo"','length': 10,'name': 'diassemoleo','precision': 3,'type': 2}],
            'INPUT': outputs['JoinAttributesByFieldValue']['OUTPUT'],
            'OUTPUT': parameters['Endponint']
        }
        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Endponint'] = outputs['RefactorFields']['OUTPUT']
        return results

    def name(self):
        return 'Endpoint'

    def displayName(self):
        return 'Endpoint'

    def group(self):
        return 'Óleo'

    def groupId(self):
        return 'Óleo'

    def createInstance(self):
        return Endpoint()
