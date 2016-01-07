# coding: utf-8
#!/usr/bin/python
import time
import requests
import simplejson
import os, re

from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime
from sys import stderr
from re import findall

# ENUMS
class FieldType:
    GROUP_FIELD = 1
    ONE_FIELD = 2

class FieldsType:
    NON_REPETITIVE_FIELDS = 3
    REPETITIVE_FIELDS = 4

class ImportData:
    MONGO = 1
    REST = 2


class Form(object):    

    '''
    Base class of Form take as argument an object with metadata values and answers
    '''
    def __init__(self, **kwargs):
        self.form_id = kwargs["form_id"]        
        self.geolocation = kwargs["geolocation"]
        self.start_timestamp = kwargs["start_timestamp"]
        self.end_timestamp = kwargs["start_timestamp"]
        self.created_at = kwargs["created_at"]
        self.answers = kwargs["answers"]


    def __str__(self):
        return "------------\nProperties of Form\nFORM ID: {0}\nGEOLOCATION: {1}\nSTART\
        TIMESTAMP: {2}\nEND TIMESTAMP: {3}\nCREATED AT: {4}\nANSWERS: {5}\n-------------".\
        format(self.form_id, self.geolocation, self.start_timestamp, self.end_timestamp, self.created_at, self.answers)
        
    def get_form(self):
        '''
        Get the values of the object Form as a dictionary
        '''
        return {
            "form_id" : self.form_id,
            "geolocation" : self.geolocation,
            "start_timestamp" : self.start_timestamp,
            "end_timestamp" : self.end_timestamp,
            "created_at" : self.created_at,
            "answers" : self.answers
        }
        
    def get_answer_for_field_id(self, answers_key, answer, field_id, field_type=''):
        '''
        Get the answer of a field id; given a list of the posible answers, the answer and the field
        '''    
        records = list()
        for ids in answers_key:
            ids = ids.replace(' ', '')
            if field_id == ids:
                records.append(ids)
                
        if len(records) == 1:
            if field_type=='int':
                try:
                    return int(answer[records[0]])
                except ValueError:
                    return answer[records[0]]
            elif field_type=='float':
                try:
                    return float(answer[records[0]])
                except ValueError:
                    return answer[records[0]]
            elif field_type=='date':
                try:
                    return self.convert_to_sting_date(answer[records[0]])
                except ValueError:
                    return answer[records[0]]                
            else:
                return answer[records[0]].decode("latin-1")
        else:
            return ""

    def clean_file_structure(self, file_structure):
        answers = {}
        for key in file_structure['answers']:
            if file_structure['answers'][key]:
                answers.update({key:file_structure['answers'][key]})
        file_structure['answers'] = answers
        return file_structure

    def convert_to_epoch(self, strisodate):
        strisodate2 = re.sub(' ','',strisodate)
        strisodate2 = strisodate2.split(' ')[0]
        try:
            date_object = datetime.strptime(strisodate2, '%Y-%m-%d')
        except ValueError:
            date_object = datetime.strptime(strisodate2[:8],  '%d/%m/%y')        
        return int(date_object.strftime("%s"))
        

    def convert_to_sting_date(self, strisodate):
        strisodate2 = re.sub(' ','',strisodate)
        strisodate2 = strisodate2.split(' ')[0]
        try:
            date_object = datetime.strptime(strisodate2, '%Y-%m-%d')
        except ValueError:
            date_object = datetime.strptime(strisodate2[:8],  '%d/%m/%y')
        return date_object.strftime('%Y-%m-%d')

    
class SanfandilaForm(Form):

    ALIMENTO_RECIBIDO = 3015
    PESO_SEMANAL = 4627
    ABC_LOTES = 4886    
    ALIMENTO_CONSUMO_DIARIO = 3295
    PEDIDO_ALIMENTO_SEMANAL = 2925
    VENTAS_Y_TRASPASOS = 2754
    CERDOS_RECIBIDOS = 2760
    MORTALIDADES_MODULOS = 3288
    MORTALIDADES_SANFANDILA_ABC = 4706
    PARAMETROS = 4879
    CAPACIDAD_LAGOS = 1234
    TESTING = 5106
    
    def __init__(self, **kwargs):        
        super(SanfandilaForm, self).__init__(**kwargs)
        if self.form_id is None:
            self.form_id = self.get_form_id(kwargs["file_path"])
        

    def __str__():
        return super(SanfandilaForm, self).__str__()
    
    def get_form(self):
        return self.clean_file_structure({
            "form_id" : self.form_id,
            "geolocation" : self.geolocation,
            "start_timestamp" : self.start_timestamp,
            "end_timestamp" : self.end_timestamp,
            "answers" : self.get_answers()
            #"created_at" : self.convert_to_epoch(self.created_at),
        })

    def get_form_id(self, filename):
        form_id_filenames_map = {
            self.ALIMENTO_RECIBIDO : 'alimento_recibido',
            self.PESO_SEMANAL : 'peso_semanal',
            self.ABC_LOTES : 'abc_lotes',
            self.ALIMENTO_CONSUMO_DIARIO : 'alimento_consumo_diario',
            self.ALIMENTO_RECIBIDO : 'alimento_recibido',                        
            self.PEDIDO_ALIMENTO_SEMANAL : 'pedido_alimento_semanal',            
            self.VENTAS_Y_TRASPASOS : 'ventas_y_traspasos',            
            self.CERDOS_RECIBIDOS : 'cerdos_recibidos',            
            self.MORTALIDADES_MODULOS : 'mortalidades_modulos',            
            self.MORTALIDADES_SANFANDILA_ABC : 'mortalidades_sanfandila_abc',
            self.PARAMETROS : 'parametros',
            self.CAPACIDAD_LAGOS : 'capacidad_lagos',
            self.TESTING : 'testing'
        }        

        for key, value in form_id_filenames_map.iteritems():
            if value in filename:
                return key
        raise ValueError("invalid filename!")
    
    
    def get_answers(self):
        answer_keys = self.answers.keys()
        if self.created_at is None:
            try:
                self.created_at = self.get_answer_for_field_id(answer_keys, self.answers, 'fecha_creacion', '')
            except:
                self.created_at = ''
        return self.recursive_extraction_answers(self.get_variables_definition(), answer_keys)


    def recursive_extraction_answers(self, configuration, answer_keys):
        answers = {}
        delimiter()
        print "answer_keys: ",answer_keys
        delimiter()
        for item in configuration:
            if isinstance(item, dict):                
                for field_form_file, field_form_collection in item.iteritems():
                    if field_form_collection[0] == FieldType.ONE_FIELD:
                        result = self.get_answer_for_field_id(answer_keys, self.answers, field_form_file, field_form_collection[2])
                        if field_form_collection[2] == 'int' and result == '':
                            result = 0                
                        answers[field_form_collection[1]] = result
                        
                    elif field_form_collection[0] == FieldType.GROUP_FIELD:
                        try:
                            answers_in_group = field_form_file.split(',')
                            answers_list_group = list()
                            for answer in answers_in_group:
                                answers_list_group.append(self.get_answer_for_field_id(answer_keys, self.answers, field_form_file, field_form_collection[2]))
                            answers[field_form_collection[1]] = answers_list_group
                        except:
                            raise TypeError("Error to parse a multiple field")
                    elif field_form_collection[0] == FieldsType.REPETITIVE_FIELDS:
                        answers[field_form_collection[1]] = [self.recursive_extraction_answers(field_form_collection, answer_keys)]
                    else:
                        raise TypeError("Error to parse configuration")
        return answers

            
                            
    
    def get_variables_definition(self):
        form_id_fields_map =  {
            self.ALIMENTO_RECIBIDO : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'alimento' : (FieldsType.REPETITIVE_FIELDS, '301500000000000000000003', {
                    'tipo_alimento' : (FieldType.ONE_FIELD, '301500000000000000000004', ''),
                    'origen_alimento' : (FieldType.ONE_FIELD, '301500000000000000000005', ''),
                    'cantidad' : (FieldType.ONE_FIELD, '301500000000000000000006', 'int')
                })
            }],

            self.PESO_SEMANAL : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'tamano_muestra' : (FieldType.ONE_FIELD, '462700000000000000000003', 'float'),
                'kilos_total' : (FieldType.ONE_FIELD, '462700000000000000000004', 'float'),
                'edad_sem' : (FieldType.ONE_FIELD, '462700000000000000000005', 'int')                
            }],
            
            self.ABC_LOTES : [{
                'fecha_inicio' : (FieldType.ONE_FIELD, '000000000000000000000001', ''),                
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'lote' : (FieldType.ONE_FIELD, '488600000000000000000003', ''),
                'etapa' : (FieldType.ONE_FIELD, '488600000000000000000004', ''),
                'flujo' : (FieldType.ONE_FIELD, '488600000000000000000005', ''),
                'estatus' : (FieldType.ONE_FIELD, '488600000000000000000006', ''),
            }],
            
            self.ALIMENTO_CONSUMO_DIARIO : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'alimento' : (FieldsType.REPETITIVE_FIELDS, '329500000000000000000003', {
                    'tipo_alimento' : (FieldType.ONE_FIELD, '329500000000000000000004', ''),
                    'lote' : (FieldType.ONE_FIELD, '329500000000000000000005', 'float'),                    
                    'kilos' : (FieldType.ONE_FIELD, '329500000000000000000006', 'float')
                })
            }],
            
            self.PEDIDO_ALIMENTO_SEMANAL : [{
                'numero_semana_pedido' : (FieldType.ONE_FIELD, '292500000000000000000001', ''),
                'granja' : (FieldType.ONE_FIELD, '292500000000000000000002', ''),
                'pedido_alimento' : (FieldsType.REPETITIVE_FIELDS, '292500000000000000000003', {
                    'tipo_alimento' : (FieldType.ONE_FIELD, '292500000000000000000004', ''),
                    'cantidad' : (FieldType.ONE_FIELD, '292500000000000000000005', 'float'),
                    'dia' : (FieldType.ONE_FIELD, '292500000000000000000006', ''),                    
                })
            }],
            
            self.VENTAS_Y_TRASPASOS : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),                
                'tipo_movimiento' : (FieldsType.REPETITIVE_FIELDS, '275400000000000000000003', {
                    'movimiento' : (FieldType.ONE_FIELD, '275400000000000000000004', ''),
                    'traspaso_granja_destino' : (FieldType.ONE_FIELD, '275400000000000000000005', ''),
                    'cantidad' : (FieldType.ONE_FIELD, '275400000000000000000006', 'int'),
                    'kilos_totales' : (FieldType.ONE_FIELD, '275400000000000000000007', 'int'),
                    'dias_totales' : (FieldType.ONE_FIELD, '275400000000000000000008', 'int'),
                    'lote' : (FieldType.ONE_FIELD, '275400000000000000000009', ''),
                    'flujo' : (FieldType.ONE_FIELD, '275400000000000000000010', '')
                })
            }],

            self.CERDOS_RECIBIDOS : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'flujo' : (FieldType.ONE_FIELD, '276000000000000000000003', ''),
                'granja_origen' : (FieldType.ONE_FIELD, '276000000000000000000004', ''),
                'lote' : (FieldType.ONE_FIELD, '276000000000000000000005', ''),
                'cerdos_recibidos' : (FieldType.ONE_FIELD, '276000000000000000000006', 'float'),
                'kilos_total' : (FieldType.ONE_FIELD, '276000000000000000000007', 'float'),
                'edad_total' : (FieldType.ONE_FIELD, '276000000000000000000008', 'float')
            }],

            self.MORTALIDADES_MODULOS : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'total_muertos' : (FieldType.ONE_FIELD, '328800000000000000000003', ''),
                'descripcion_muertes' : (FieldsType.REPETITIVE_FIELDS, '328800000000000000000004', {
                    'causa_muerte' : (FieldType.ONE_FIELD, '328800000000000000000005', ''),
                    'muerto_por_esta_causa' : (FieldType.ONE_FIELD, '328800000000000000000006', ''),
                    'lote' : (FieldType.ONE_FIELD, '328800000000000000000007', ''),
                    'flujo' : (FieldType.ONE_FIELD, '328800000000000000000008', '')
                })                
            }],

            self.MORTALIDADES_SANFANDILA_ABC : [{
                'fecha' : (FieldType.ONE_FIELD, '000000000000000000000001', 'date'),
                'granja' : (FieldType.ONE_FIELD, '000000000000000000000002', ''),
                'total_muertos' : (FieldType.ONE_FIELD, '470600000000000000000003', 'int'),
                'descripcion_muertes' : (FieldsType.REPETITIVE_FIELDS, '470600000000000000000004', {
                    'causa_muerte' : (FieldType.ONE_FIELD, '470600000000000000000005', ''),
                    'muerto_por_esta_causa' : (FieldType.ONE_FIELD, '470600000000000000000006', ''),
                    'lote' : (FieldType.ONE_FIELD, '470600000000000000000007', ''),
                    'flujo' : (FieldType.ONE_FIELD, '470600000000000000000008', '')
                })
            }],

            self.PARAMETROS : [{
                'sem_edad' : (FieldType.ONE_FIELD, '487900000000000000000001', 'float'),
                'alimento_consumo_semanal' : (FieldType.ONE_FIELD, '487900000000000000000002', 'float'),
                'alimento_consumo_diario' : (FieldType.ONE_FIELD, '487900000000000000000003', 'float'),
                'ganancia_diaria' : (FieldType.ONE_FIELD, '487900000000000000000004', 'float'),
                'gsp' : (FieldType.ONE_FIELD, '487900000000000000000005', 'float'),
                'peso' : (FieldType.ONE_FIELD, '487900000000000000000006', 'float'),
                'porcentaje_desecho' : (FieldType.ONE_FIELD, '487900000000000000000007', 'float'),
                'peso_retrasado' : (FieldType.ONE_FIELD, '487900000000000000000008', 'float'),
                'conversion_alimenticia' : (FieldType.ONE_FIELD, '487900000000000000000009', 'float'),
                'mortalidad' : (FieldType.ONE_FIELD, '487900000000000000000010', 'float'),
                'consumo_semanal' : (FieldType.ONE_FIELD, '487900000000000000000011', 'float'),
                'consumo_diario' : (FieldType.ONE_FIELD, '487900000000000000000012', 'float'),
                'kg_carne' : (FieldType.ONE_FIELD, '487900000000000000000013', 'float'),
                'dias_edad' : (FieldType.ONE_FIELD, '487900000000000000000014', 'float'),
                'sitios' : (FieldType.ONE_FIELD, '487900000000000000000015', ''),
                'alimento' : (FieldType.ONE_FIELD, '487900000000000000000016', ''),
                'consumo_alimento' : (FieldType.ONE_FIELD, '487900000000000000000017', 'float'),
                'peso_desecho' : (FieldType.ONE_FIELD, '487900000000000000000018', 'float'),
                'porcentaje_desecho' : (FieldType.ONE_FIELD, '487900000000000000000019', 'float'),
                'inventario_inicial' : (FieldType.ONE_FIELD, '487900000000000000000020', 'float'),
                'inventario_final' : (FieldType.ONE_FIELD, '487900000000000000000021', 'float'),
                'inventario_desecho' : (FieldType.ONE_FIELD, '487900000000000000000022', 'float'), 
                'inventario_retrasado' : (FieldType.ONE_FIELD, '487900000000000000000023', 'float'),
                'cantidad_alimento_consumido' : (FieldType.ONE_FIELD, '487900000000000000000024', 'float'),
                'cantidad_alimento_acumulado' : (FieldType.ONE_FIELD, '487900000000000000000025', 'float')
            }],

            self.CAPACIDAD_LAGOS : [{
                'capacidad' : (FieldType.ONE_FIELD, '123400000000000000000001', 'float'),
                'granja' : (FieldType.ONE_FIELD, '123400000000000000000002', '')
            }],
            
            self.TESTING : [{
                'testing' : (FieldType.ONE_FIELD, '012345678901234567890123', ''),
                'testing2' : (FieldType.ONE_FIELD, '012345678901234567890124', '')                
            }]

        }
        return form_id_fields_map[self.form_id]


            # self.PARAMETROS : [{
            #     'sem_edad' : (FieldType.ONE_FIELD, '487900000000000000000001', 'float'),
            #     'alimento_consumo_semanal' : (FieldType.ONE_FIELD, '487900000000000000000002', 'float'),
            #     'alimento_consumo_diario' : (FieldType.ONE_FIELD, '487900000000000000000003', 'float'),
            #     'ganancia_diaria' : (FieldType.ONE_FIELD, '487900000000000000000004', 'float'),
            #     'gsp' : (FieldType.ONE_FIELD, '487900000000000000000005', 'float'),
            #     'peso' : (FieldType.ONE_FIELD, '487900000000000000000006', 'float'),
            #     'porcentaje_desecho' : (FieldType.ONE_FIELD, '487900000000000000000007', 'float'),
            #     'peso_retrasado' : (FieldType.ONE_FIELD, '487900000000000000000008', 'float'),
            #     'conversion_alimenticia' : (FieldType.ONE_FIELD, '487900000000000000000009', 'float'),
            #     'mortalidad' : (FieldType.ONE_FIELD, '487900000000000000000010', 'float'),
            #     'consumo_semanal' : (FieldType.ONE_FIELD, '487900000000000000000011', 'float'),
            #     'consumo_diario' : (FieldType.ONE_FIELD, '487900000000000000000012', 'float'),
            #     'kg_carne' : (FieldType.ONE_FIELD, '487900000000000000000013', 'float'),
            #     'semana_calendario' : (FieldType.ONE_FIELD, '487900000000000000000014', 'float')                
            # }],

    
def warning(*objs):
    '''
    To print stuff at stderr
    '''
    output = "warning:%s\n" % objs
    stderr.write(output)


def load_answers(metadata, file_path):
    load_file = get_file_to_import(file_path)
    answers = []
    for answer_line in load_file:
        form = SanfandilaForm(
            **{
                "file_path" : file_path,
                "form_id" : metadata['form_id'],
                "geolocation" : [metadata['lat'], metadata['glong']],
                "start_timestamp" : metadata['start_timestamp'],
                "end_timestamp" : metadata['start_timestamp'],
                "created_at" : metadata['created_at'],
                "answers" : answer_line
            }
        )
        answers.append(form.get_form())
    return answers

def login(session, username, password):
    r = session.post(config['LOGIN_URL'], data = simplejson.dumps({"password": config['PASS'], "username": config['USERNAME']}))
    return r.status_code == 200


def post_answers(session, answers):
    POST_CORRECTLY=0
    errors_json = []
    for index, answer in enumerate(answers):
        if config['IS_USING_APIKEY']:
            r = session.post(config['FORM_ANSWER_URL'], data = simplejson.dumps(answer, encoding='latin-1'), headers={'Content-type': 'application/json', 'Authorization':'ApiKey {0}:{1}'.format(config['AUTHORIZATION_EMAIL_VALUE'], config['AUTHORIZATION_TOKEN_VALUE'])}, verify=False)
        else:
            r = session.post(config['FORM_ANSWER_URL'], data = simplejson.dumps(answer, encoding='latin-1'), headers={'Content-type': 'application/json'}, verify=False)
        if r.status_code == 201:
            print "Answer %s saved."%(index + 1)
            POST_CORRECTLY += 1
        else:
            print "Answer %s was rejected."%(index + 1)
            print 'r.content', r.content
            response = simplejson.loads(r.content)
            errors_json.append(response)
    print 'Se importaron correctamente %s de %s registros'%(POST_CORRECTLY, index+1)
    if errors_json:
        print 'errors_json=', errors_json

def get_file_to_import(file_path):
    answers = []
    with open(file_path) as file:
        headers = file.readline().strip().split(',')
        for line in file:
            line = line.strip().split(',')
            field_map = zip(headers, line)
            answers.append(dict(field_map))
    print answers
    return answers



def get_user_connection(user_id):
    print "> Getting connection ..."
    connection = {}    
    connection['client'] = MongoClient(config['HOST'], config['PORT'])
    user_db_name = "infosync_answers_client_{0}".format(user_id)
    if not user_db_name:
        return None
    connection['db'] = connection['client'][user_db_name]
    return connection

def create_collection(collection, user_connection):
    print "> Creating Collection ..."
    if config['CREATE'] and collection in user_connection['db'].collection_names():
        oldCollection = user_connection['db'][collection]
        oldCollection.drop()
    newCollection = Collection(user_connection['db'], collection, create=config['CREATE'])
    return newCollection

    

def upload_answers_to_database(answers):
    print "> Uploading Content ..."    
    user_connection = get_user_connection(config['USER_ID'])
    collection = create_collection(config['COLLECTION'], user_connection)
    counter = 0
    for answer in answers:
        try:
            document = collection.insert(answer)
        except:
            pass
            #print "The document {0} was not inserted".format(answer)
        finally:
            counter = counter +1
    print counter

    
def upload_answers_using_rest(answers):
    session = requests.Session()
    if config['IS_USING_APIKEY']:
        post_answers(session, answers,)
    else:
        # Log In
        if login(session, config['USERNAME'], config['PASS']):                    
            print "User logged in.",
            post_answers(session, answers, )
        else:
            print "Invalid login."

def delimiter():
    print "="*50

config = {
    'FORM_ANSWER_URL' : 'https://grover.info-sync.com/api/infosync/form_answer/',        
    'LOGIN_URL' : 'https://grover.info-sync.com/api/infosync/user_admin/login/',
    'USERNAME' : 'infosync@sanfandila.com',
    'PASS' : '123456',
    'COLLECTION' : 'form_answer',
    'HOST' : 'localhost',
    'PORT' : 27019,
    'USER_ID' : 'demo',
    'KEYS_POSITION' : {},
    'FILE_PATH_DIR' : 'tmp/',
    'IS_USING_APIKEY' : True,
    'AUTHORIZATION_EMAIL_VALUE' : 'infosync@sanfandila.com',
    'AUTHORIZATION_TOKEN_VALUE' : '530bd4396d7ffd9f6ee76aea4f621e7d00cd9e21',
    'LOAD_DATA_USING' : ImportData.REST,
    'CREATE' : False
}
    

# Sanfandila APIKEY TOKEN
# AUTHORIZATION_EMAIL_VALUE = 'jefatura.ti@sanfandila.com'
# AUTHORIZATION_TOKEN_VALUE = 'fd390bd5e5297edf3a3fa0b759919e88a9334709'


if __name__ == "__main__":
    files = os.popen('ls %s' % config['FILE_PATH_DIR'])    
    all_files = files.read().split('\n')
    for file_name in all_files:
        if file_name:
            file_path = config['FILE_PATH_DIR'] + file_name
            print "Filename: {0}".format(file_path)
            time_started = time.time()
            metadata = {
                'form_id' : None,
                'lat' : 25.644885499999997,
                'glong' : -100.3862645,
                'start_timestamp' : 123456789,
                'created_at' : None
            }
            answers = loadgit_answers(metadata, file_path)
            print "Total answers: ",len(answers)
            try:
                delimiter()
                print "Sample of answers:"
                print answers[0]
                print answers[1]
                print answers[2]
                print answers[3]
            except:
                pass
            finally:
                delimiter()
            if len(answers) > 0:
                print "%s answers loaded." % len(answers)                            
                if config['LOAD_DATA_USING'] == ImportData.MONGO:
                    upload_answers_to_database(answers)
                elif config['LOAD_DATA_USING'] == ImportData.REST:
                    upload_answers_using_rest(answers)
                else:
                    raise ValueError("LOAD_DATA_USING {0} is invalid".format(config['LOAD_DATA_USING']))
            else:
                 "No answers loaded."
