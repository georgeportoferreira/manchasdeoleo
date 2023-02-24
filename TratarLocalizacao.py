"""
Model exported as python.
Name : 2. Tratar localização
Group : Óleo
With QGIS : 32216
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class TratarLocalizao(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('relatoriodevistoria', 'RV de hoje', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('rvdeontem', 'RV de ontem', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('zonas', 'Zonas', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Tratarmanualmente', 'TratarManualmente', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Rv3ok', 'RV3OK', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(16, model_feedback)
        results = {}
        outputs = {}

        # Calcula distancia da zona
        alg_params = {
            'FIELD': 'loc_id',
            'HUBS': parameters['zonas'],
            'INPUT': parameters['relatoriodevistoria'],
            'UNIT': 0,  # Meters
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculaDistanciaDaZona'] = processing.run('qgis:distancetonearesthubpoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # 0. Sel RV OK
        alg_params = {
            'INPUT': outputs['CalculaDistanciaDaZona']['OUTPUT'],
            'INTERSECT': parameters['zonas'],
            'METHOD': 0,  # creating new selection
            'PREDICATE': 6,  # are within
        }
        outputs['SelRvOk'] = processing.run('native:selectbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Grava RV OK
        alg_params = {
            'INPUT': outputs['CalculaDistanciaDaZona']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GravaRvOk'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # 1.Selecionar RV fora da zona
        alg_params = {
            'INPUT': outputs['CalculaDistanciaDaZona']['OUTPUT'],
            'INTERSECT': parameters['zonas'],
            'METHOD': 0,  # creating new selection
            'PREDICATE': 2,  # disjoint
        }
        outputs['SelecionarRvForaDaZona'] = processing.run('native:selectbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # 2.RV fora da Zona
        alg_params = {
            'INPUT': outputs['CalculaDistanciaDaZona']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RvForaDaZona'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # 3. RVcF
        alg_params = {
            'INPUT': outputs['RvForaDaZona']['OUTPUT'],
            'MFIELD': None,
            'TARGET_CRS': 'ProjectCrs',
            'XFIELD': 'x',
            'YFIELD': 'y',
            'ZFIELD': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rvcf'] = processing.run('qgis:createpointslayerfromtable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # 4. Selecionar RV com coordenada da foto na zona
        alg_params = {
            'INPUT': outputs['Rvcf']['OUTPUT'],
            'INTERSECT': parameters['zonas'],
            'METHOD': 0,  # creating new selection
            'PREDICATE': 0,  # intersect
        }
        outputs['SelecionarRvComCoordenadaDaFotoNaZona'] = processing.run('native:selectbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # 5. RVcF na zona
        alg_params = {
            'INPUT': outputs['Rvcf']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RvcfNaZona'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # 6. sel RVcF fora da zona
        alg_params = {
            'INPUT': outputs['Rvcf']['OUTPUT'],
            'INTERSECT': parameters['zonas'],
            'METHOD': 0,  # creating new selection
            'PREDICATE': 2,  # disjoint
        }
        outputs['SelRvcfForaDaZona'] = processing.run('native:selectbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # 7. RVcF fora da Zona
        alg_params = {
            'INPUT': outputs['Rvcf']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RvcfForaDaZona'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # cria idjoin p RV hoje
        alg_params = {
            'FIELD_LENGTH': 254,
            'FIELD_NAME': 'idjoin',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat( "Name",\'-\',left ( "Município" ,length( "Município" )-1),\'-\',left ( "estado" ,length( "estado" )-1))',
            'INPUT': outputs['RvcfForaDaZona']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriaIdjoinPRvHoje'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # cria idjoin p RV ontem
        alg_params = {
            'FIELD_LENGTH': 254,
            'FIELD_NAME': 'idjoin',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat("localidade",\'-\',"municipio",\'-\',"estado")',
            'INPUT': parameters['rvdeontem'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CriaIdjoinPRvOntem'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # JoinPeloNome
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELD': 'idjoin',
            'FIELDS_TO_COPY': None,
            'FIELD_2': 'idjoin',
            'INPUT': outputs['CriaIdjoinPRvOntem']['OUTPUT'],
            'INPUT_2': outputs['CriaIdjoinPRvHoje']['OUTPUT'],
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Joinpelonome'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # semJoin
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'idjoin',
            'FIELDS_TO_COPY': None,
            'FIELD_2': 'idjoin',
            'INPUT': outputs['CriaIdjoinPRvHoje']['OUTPUT'],
            'INPUT_2': outputs['CriaIdjoinPRvOntem']['OUTPUT'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': '',
            'NON_MATCHING': parameters['Tratarmanualmente']
        }
        outputs['Semjoin'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Tratarmanualmente'] = outputs['Semjoin']['NON_MATCHING']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # TratarCamposJPN
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"Data"','length': 254,'name': 'Data','precision': 0,'type': 10},{'expression': '"Hora_2"','length': 254,'name': 'Hora','precision': 0,'type': 10},{'expression': '"Name"','length': 254,'name': 'Name','precision': 0,'type': 10},{'expression': '"Município"','length': 254,'name': 'Município','precision': 0,'type': 10},{'expression': '"Estado_2"','length': 254,'name': 'Estado','precision': 0,'type': 10},{'expression': '"Status_2"','length': 254,'name': 'Status','precision': 0,'type': 10},{'expression': '"SubmisID"','length': 20,'name': 'SubmisID','precision': 0,'type': 6},{'expression': '"Imagem"','length': 254,'name': 'Imagem','precision': 0,'type': 10},{'expression': '"Nome"','length': 254,'name': 'Nome','precision': 0,'type': 10},{'expression': '"Sobrenome"','length': 254,'name': 'Sobrenome','precision': 0,'type': 10},{'expression': '"Instituica"','length': 254,'name': 'Instituica','precision': 0,'type': 10},{'expression': '"equipe_no_"','length': 254,'name': 'equipe_no_','precision': 0,'type': 10},{'expression': '"limpeza_co"','length': 254,'name': 'limpeza_co','precision': 0,'type': 10},{'expression': '"x"','length': 10,'name': 'x','precision': 6,'type': 6},{'expression': '"y"','length': 10,'name': 'y','precision': 6,'type': 6},{'expression': '"idjoin"','length': 254,'name': 'idjoin','precision': 0,'type': 10}],
            'INPUT': outputs['Joinpelonome']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Tratarcamposjpn'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # RVOK_JPN_RVcF
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['Tratarcamposjpn']['OUTPUT'],outputs['RvcfNaZona']['OUTPUT'],outputs['GravaRvOk']['OUTPUT']],
            'OUTPUT': parameters['Rv3ok']
        }
        outputs['Rvok_jpn_rvcf'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Rv3ok'] = outputs['Rvok_jpn_rvcf']['OUTPUT']
        return results

    def name(self):
        return '2. Tratar localização'

    def displayName(self):
        return '2. Tratar localização'

    def group(self):
        return 'Óleo'

    def groupId(self):
        return 'Óleo'

    def createInstance(self):
        return TratarLocalizao()
