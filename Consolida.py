"""
Model exported as python.
Name : 3. Gerar consolidado
Group : Óleo
With QGIS : 32216
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class GerarConsolidado(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('relatoriodevistoria', 'RV3OK', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('rvdeontem', 'RV de ontem', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('tratadomanualmente', 'TratadoManualmente', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('zonas', 'Zonas', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Localidade_atualizado', 'localidade_atualizado', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Areas_oleadas', 'AREAS_OLEADAS', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue='memory:'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(25, model_feedback)
        results = {}
        outputs = {}

        # Mesclar RV de hoje
        alg_params = {
            'CRS': None,
            'LAYERS': [parameters['relatoriodevistoria'],parameters['tratadomanualmente']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarRvDeHoje'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # ontemXzona
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['zonas'],
            'JOIN': parameters['rvdeontem'],
            'JOIN_FIELDS': '',
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREDICATE': 0,  # intersects
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Ontemxzona'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # hojeXzona
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['Ontemxzona']['OUTPUT'],
            'JOIN': outputs['MesclarRvDeHoje']['OUTPUT'],
            'JOIN_FIELDS': None,
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREDICATE': 0,  # intersects
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Hojexzona'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # eliminaLocalNuncaTocado
        alg_params = {
            'EXPRESSION': '("localidade_2" is not null) or  "Name" is not null',
            'INPUT': outputs['Hojexzona']['OUTPUT'],
            'METHOD': 0,  # creating new selection
        }
        outputs['Eliminalocalnuncatocado'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # LocalidadeTocada
        alg_params = {
            'INPUT': outputs['Eliminalocalnuncatocado']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Localidadetocada'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # selecionaRVhoje
        alg_params = {
            'FIELD': 'Name',
            'INPUT': outputs['Localidadetocada']['OUTPUT'],
            'METHOD': 0,  # creating new selection
            'OPERATOR': 9,  # is not null
            'VALUE': ''
        }
        outputs['Selecionarvhoje'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # AtualizaDataRevis
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Data_Revis',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 3,  # Date
            'FORMULA': 'if (Data is null, Data_Revis, to_date(concat(right("Data",4),\'-\',substr("Data",4,2),\'-\',left("Data",2))))',
            'INPUT': outputs['Selecionarvhoje']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Atualizadatarevis'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # AtualizaHora
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Hora',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'Hora_2',
            'INPUT': outputs['Atualizadatarevis']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Atualizahora'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # AtualizaStatus
        alg_params = {
            'FIELD_LENGTH': 254,
            'FIELD_NAME': 'Status',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'if (Status_2 is null, Status, Status_2)',
            'INPUT': outputs['Atualizahora']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Atualizastatus'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # eliminaVistoriaSemOleo
        alg_params = {
            'EXPRESSION': "not ((localidade is null) and status =  'Óleo - Não Observado' )",
            'INPUT': outputs['Atualizastatus']['OUTPUT'],
            'METHOD': 0,  # creating new selection
        }
        outputs['Eliminavistoriasemoleo'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # EliminadoVistSemOleo
        alg_params = {
            'INPUT': outputs['Eliminavistoriasemoleo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Eliminadovistsemoleo'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # PopulaDataAvist
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Data_Avist',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 3,  # Date
            'FORMULA': 'if (Data_Avist is null, Data_Revis, Data_Avist)',
            'INPUT': outputs['Eliminadovistsemoleo']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Populadataavist'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # PopulaLocalidade
        alg_params = {
            'FIELD_LENGTH': 254,
            'FIELD_NAME': 'localidade',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'if (localidade is null, Name, localidade)',
            'INPUT': outputs['Populadataavist']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Populalocalidade'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # CriaCampoEscolha
        alg_params = {
            'FIELD_LENGTH': 12,
            'FIELD_NAME': 'escolha',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'concat(Data_Revis, (CASE \r\n  WHEN  "Status"=   \'Oleada - Manchas\'  THEN 2\r\n  WHEN  "Status"= \'Oleada - Vestígios/Esparsos\' THEN 1  \r\n  ELSE 0\r\nEND))',
            'INPUT': outputs['Populalocalidade']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Criacampoescolha'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Escolhe
        alg_params = {
            'FIELD_LENGTH': 12,
            'FIELD_NAME': 'escolhido',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'maximum( escolha, loc_id)',
            'INPUT': outputs['Criacampoescolha']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Escolhe'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # SelecionaEscolhidos
        alg_params = {
            'EXPRESSION': 'Escolha = Escolhido',
            'INPUT': outputs['Escolhe']['OUTPUT'],
            'METHOD': 0,  # creating new selection
        }
        outputs['Selecionaescolhidos'] = processing.run('qgis:selectbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # EntregaEscolhidos
        alg_params = {
            'INPUT': outputs['Selecionaescolhidos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Entregaescolhidos'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"geocodigo"','length': 15,'name': 'geocodigo','precision': 0,'type': 10},{'expression': '"localidade"','length': 254,'name': 'localidade','precision': 0,'type': 10},{'expression': '"loc_id"','length': 12,'name': 'loc_id','precision': 0,'type': 10},{'expression': '"municipio"','length': 100,'name': 'municipio','precision': 0,'type': 10},{'expression': '"estado"','length': 100,'name': 'estado','precision': 0,'type': 10},{'expression': '"sigla_uf"','length': 3,'name': 'sigla_uf','precision': 0,'type': 10},{'expression': '"Data_Avist"','length': 10,'name': 'Data_Avist','precision': 0,'type': 14},{'expression': '"Data_Revis"','length': 10,'name': 'Data_Revis','precision': 0,'type': 14},{'expression': '"Status"','length': 30,'name': 'Status','precision': 0,'type': 10},{'expression': '"Latitude"','length': 20,'name': 'Latitude','precision': 0,'type': 10},{'expression': '"Longitude"','length': 20,'name': 'Longitude','precision': 0,'type': 10},{'expression': '"Hora"','length': 10,'name': 'Hora','precision': 0,'type': 10}],
            'INPUT': outputs['Entregaescolhidos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # EliminarDuplicatas
        alg_params = {
            'FIELD': 'loc_id',
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Eliminarduplicatas'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Point on surface
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['Eliminarduplicatas']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PointOnSurface'] = processing.run('native:pointonsurface', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Calcula Latitude
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'Latitude',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE WHEN $y<0\nTHEN (floor ($y*-1) || \'° \' || floor((($y*-1) - floor ($y*-1)) * 60) ||\'\\\' \' || substr( (tostring(((($y*-1) - floor ($y*-1)) * 60) - floor((($y*-1) - floor ($y*-1)) * 60)) * 60),1,5) || \'" S\')\nELSE (floor ($y) || \'° \' || floor((($y) - floor ($y)) * 60) ||\'\\\' \' || substr( (tostring(((($y) - floor ($y)) * 60) - floor((($y) - floor ($y)) * 60)) * 60),1,5) || \'" N\')\nEND',
            'INPUT': outputs['PointOnSurface']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculaLatitude'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Calcula Longitude
        alg_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'Longitude',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'CASE WHEN $X<0\nTHEN (floor ($x*-1) || \'° \' || floor((($x*-1) - floor ($x*-1)) * 60) ||\'\\\' \' || substr( (tostring(((($x*-1) - floor ($x*-1)) * 60) - floor((($x*-1) - floor ($x*-1)) * 60)) * 60),1,5) || \'" W\')\nELSE (floor ($x) || \'° \' || floor((($x) - floor ($x)) * 60) ||\'\\\' \' || substr( (tostring(((($x) - floor ($x)) * 60) - floor((($x) - floor ($x)) * 60)) * 60),1,5) || \'" E\')\nEND',
            'INPUT': outputs['CalculaLatitude']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': parameters['Areas_oleadas']
        }
        outputs['CalculaLongitude'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Areas_oleadas'] = outputs['CalculaLongitude']['OUTPUT']

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # localidade_aXareas_oleadas
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['zonas'],
            'JOIN': outputs['CalculaLongitude']['OUTPUT'],
            'JOIN_FIELDS': 'localidade',
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREDICATE': 0,  # intersects
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Localidade_axareas_oleadas'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # populaNovasLocalidades
        alg_params = {
            'FIELD_LENGTH': 254,
            'FIELD_NAME': 'localidade',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # String
            'FORMULA': 'if (localidade is null, localidade_2,localidade)',
            'INPUT': outputs['Localidade_axareas_oleadas']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Populanovaslocalidades'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Drop field(s)
        alg_params = {
            'COLUMN': 'localidade_2',
            'INPUT': outputs['Populanovaslocalidades']['OUTPUT'],
            'OUTPUT': parameters['Localidade_atualizado']
        }
        outputs['DropFields'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Localidade_atualizado'] = outputs['DropFields']['OUTPUT']
        return results

    def name(self):
        return '3. Gerar consolidado'

    def displayName(self):
        return '3. Gerar consolidado'

    def group(self):
        return 'Óleo'

    def groupId(self):
        return 'Óleo'

    def createInstance(self):
        return GerarConsolidado()
