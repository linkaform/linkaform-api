# PYTHON
import json, psycopg2, mongo_util
from datetime import datetime
import time, urllib2
from PIL import Image
from os import path, remove

# MONGO
from bson.objectid import ObjectId
from pymongo import MongoClient

# LINKAFORM
from b2_storage import B2Connection



# user_id = 9
# local
# media_path = '/var/www/infosync-api/backend/media/'
# dev
# media_path = '/srv/slimey.info-sync.com/infosync-api/backend/media/'
# bigbird
# media_path = '/srv/bigbird.info-sync.com/infosync-api/backend/media/'
# app
media_path = '/srv/backend.linkaform.com/infosync-api/backend/media/'
file_path = 'uploads/'
absolute_path = 'https://app.linkaform.com/media/'
host_url = 'https://app.linkaform.com/'


THUMB_SIZE_H = (90, 141)
THUMB_SIZE_V = (141, 90)

# MONGO
# local
# host = 'localhost'
# port = 27017
# dev
# host = '10.1.66.19'
# port = 27019
# host = '10.1.66.14'
# port = 27014
# app
import  os
host = 'db3.linkaform.com'
port = 27017
collection_name = 'form_answer'
# cr = MongoClient('127.0.0.1', port)
cr = MongoClient(host, port)
# mongo_dbname = 'infosync_answers_client_%s'%user_id
#databases = open('/tmp/dbs.txt','r')
#databases = cr.database_names()
databases = ['infosync_answers_client_9','infosync_answers_client_565']
print 'database', databases
# POSTGRES
# local y bigbird
# postgres_dbname = 'infosync_prod'
# conn = psycopg2.connect('dbname=%s'%postgres_dbname)
# dev
# postgres_dbname = 'infosync_prod'
# postgres_host = '10.1.66.19'
# postgres_port = '5432'
# app
postgres_dbname = 'infosync'
postgres_host = 'db3.linkaform.com'
#postgres_host = '127.0.0.1'
postgres_port = '5432'
conn = psycopg2.connect('dbname=%s user=infosync password=director host=%s port=%s'%(postgres_dbname, postgres_host, postgres_port))
cur = conn.cursor()

records_with_errors = {}
databases_with_errors = []
date = datetime.strptime('2016-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
date2 = datetime.strptime('2017-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")


PIC  = open('/var/tmp/remaining_pics.txt','w')
LOST_PICS = open('/var/tmp/lost_pics.txt','w')

dbpath='/backup/infosync/2017/backup/infosync/2017/Mongoinfosync-ALLClientDB-2017-20'

def get_user_email(user_id):
    query = 'select email from users_customuser where id ={id};\n'.format(id=user_id)
    cur.execute(query)
    return cur.fetchone()[0]


def get_properties(user_id):
    try:
        query = 'select properties from users_integration where user_id ={user_id};\n'.format(user_id=user_id)
        cur.execute(query)
        return json.loads(cur.fetchone()[0])
    except:
        return None


def create_or_get_thumbnail(image, file_name):
    """
    Creates a temp thumbnail image and returns its path.
    """
    thumb_path = path.splitext(file_name)[0] + '.thumbnail'
    x, extension = path.splitext(image.name)
    try:
        image.seek(0) # move the file position
        im = Image.open(image)
        if '.png' in extension.lower():
            im.convert('RGBA')
        else:
            im.convert('RGB')
        (width, height) = im.size

        if width >= height:
            im.thumbnail(THUMB_SIZE_H, Image.ANTIALIAS)
        else:
            im.thumbnail(THUMB_SIZE_V, Image.ANTIALIAS)

        im.save(thumb_path, 'JPEG')
        return thumb_path
    except Exception as e:
        print "Cannot create thumbnail for '%s'. %s."%(image.name, e)
    return None


def create_thumbnail(thumb_name, thumbnail):
    """
    Creates and save thumbnail from the given image.
    """
    #thumb_name = path.splitext(file_name)[0] + '.thumbnail'
    thumb_path = create_or_get_thumbnail(thumbnail, thumb_name)
    thumb_up = open(thumb_path, 'r')
    return thumb_up


def get_bucket_files(bucket_id, bucket_name, folder_name):
    return storage.b2_list_file_names(bucket_id=bucket_id, max_file_count=10000, start_file_name=folder_name)


def search_in_url(file_path):
    try:
        return  urllib2.urlopen(file_path)
    except:
	return None


def upload_file(form_id, field_id ,file_path, properties, bucket_files):
    bucket_id = properties['bucket_id']
    bucket_name = properties['bucket_name']
    folder_name = properties['folder_name']
    file_url = None
    print 'upload_file/......'
    file_name = '%s/%s/%s/%s'% (folder_name,
        form_id, field_id, file_path.split('/')[-1])
    if file_name in bucket_files:
        if 'https://app.linkaform.com' in file_path:
            return  'https://f001.backblazeb2.com/file/app-linkaform/' + file_name
        print 'file already en B2'
        return None
    public_client = file_name.find('public-path')
    if public_client == 0:
	return 'https://f001.backblazeb2.com/file/app-linkaform/' + file_name
    if not 'https' in file_path:
        file_path = absolute_path + file_path
    thumb_name = file_name.rsplit('.', 1)[0] + '.thumbnail'
    file_type = file_name.rsplit('.', 1)[1].lower()
    thumb_path = file_path.rsplit('.', 1)[0] + '.thumbnail'

    local_path = search_in_url(file_path)
    if not local_path:
        file_path = file_path.replace('media/','media/Temp/')
        local_path = search_in_url(file_path)
    thumb_path_loc = search_in_url(thumb_path)
    if not thumb_path_loc:
        thumb_path = thumb_path.replace('media/','media/Temp/')
        thumb_path = search_in_url(thumb_path)
    thumb_path = thumb_path_loc
    try:
        if local_path:
            print 'UPLOADING....'
            file_url = storage.b2_save(file_name, local_path, bucket_id)
            if file_type in ('jpg','png','jpeg'):
                if not thumb_path:
                    thumb_file = create_thumbnail(thumb_name, thumb_path)
                else:
                    thumb_file = thumb_path
                # remove(local_path)
                # remove(thumb_path)
                thumb_url = storage.b2_save(thumb_name, thumb_file, bucket_id)
        return file_url
    except Exception, e:
	print 'file_name', file_name
        print 'Exception=',e
        return None


def get_new_url(user_email, file_url, record , _key, properties, bucket_files ):
    new_url = connection_id = False
    print 'get_new_url'
    if user_email in file_url:
        new_url = upload_file(record['form_id'], _key, file_url,
        properties, bucket_files)
    elif file_url:
        url_kind = absolute_path + file_path
        if not url_kind in file_url:
            url_kind = host_url + file_path
        if 'https' in file_url:
            connection_id = file_url.replace(url_kind,'').split('/')[0].split('_')[0]
        else:
            connection_id = file_url.replace(file_path,'').split('/')[0].split('_')[0]
    try:
        int(connection_id)
    except ValueError:
	if record.has_key('folio'):
		print 'recore folio', record['folio']
	else:
		print 'record _id', record['_id']
	return None
    if connection_id:
        connection_properties = get_properties(connection_id)
        connection_bucket_files = get_bucket_files(connection_properties['bucket_id'],
        connection_properties['bucket_name'], connection_properties['folder_name'])
        connection_bucket_files = [ _file['fileName'] for _file in connection_bucket_files]
        new_url = upload_file(record['form_id'], _key, file_url,
        connection_properties, connection_bucket_files)
    if new_url:
        return new_url
    else:
        return None


def check_for_file(file_url, record):
    print 'file_url', file_url

    if host_url in file_url:
	PIC.write(record['folio'] + '=' + file_url)
	PIC.write('\n')
        return False

    exists = search_in_url(file_url)
    if exists:
        return True

    exists = search_in_url(file_url)
    print 'file_url', file_url
    print 'exists',exists.code
    if exists.code == 200:
           return True
    else:
	LOST_PICS.write(record['folio'] + '=' + file_url)
        LOST_PICS.write('\n')
        return True


for dbname in databases:
    db_ended = False
    if dbname in ['infosync', 'local']:
        continue

    user_id = dbname.split('_')[-1]
    if not user_id:
        print dbname
        if dbname not in databases_with_errors:
            databases_with_errors.append(dbname)
        continue

    user_email = get_user_email(user_id)
    properties = get_properties(user_id)
    if not properties:
        print 'user_id=', user_id
        if dbname not in databases_with_errors:
            databases_with_errors.append(dbname)
        continue
    storage = B2Connection()
    bucket_files = get_bucket_files(properties['bucket_id'],
    properties['bucket_name'], properties['folder_name'])
    bucket_files = [ _file['fileName'] for _file in bucket_files]

    cur_db = mongo_util.connect_mongodb(dbname, host, port)
    cur_col = mongo_util.get_mongo_collection(cur_db, collection_name)
    cur_db_orig = mongo_util.connect_mongodb(dbname, '127.0.0.1', port)
    cur_col_orig = mongo_util.get_mongo_collection(cur_db_orig, collection_name)

    for year in [2014,2015,2016,2017]:
        if db_ended:
            continue
        months = [month + 1 for month in range(12)]
        months.reverse()
        for month in months:
            if year == 2017 and month > 2:
                continue
            if db_ended:
                continue
            date_from = datetime.strptime('%s-%02d-01 00:00:00'%(year,month), "%Y-%m-%d %H:%M:%S")
            if month+1 ==13:
		        date_to = datetime.strptime('%s-01-01 00:00:00'%(year+1), "%Y-%m-%d %H:%M:%S")
            else:
            	date_to = datetime.strptime('%s-%02d-01 00:00:00'%(year, month+1), "%Y-%m-%d %H:%M:%S")
            print 'date from', date_from
            print 'date to', date_to

            # Base de datos en donde se hará el update
            query = {'deleted_at':{'$exists':0}, 'created_at':{'$gte':date_from,'$lt':date_to}}
            # Base de datos de donde se va a copiar el registro
            #query_check = {'deleted_at':{'$exists':0}, 'created_at':{'$lt':date_from}}
            #result_check = mongo_util.get_collection_objects(cur_col, query_check)
            #if result_check == 0:
            #    databases.remove(dbname)
            #    db_ended = True
            #    print dbname , 'was removed'
            print 'query', query
            result = mongo_util.get_collection_objects(cur_col, query)
            print 'cont=',result.count()
            records = [record for record in result]
            i = 0
            print 'dbname', dbname
            for record in records:
                i += 1
                #if i % 300 == 0:
                    #print i
                if not record.get('answers', None):
                    continue

                for _key in record['answers']:
                    if isinstance(record['answers'][_key], dict):
                        if 'file_url' in record['answers'][_key].keys():
                            new_url = None
                            already_in_b2 = False
                            file_url = record['answers'][_key]['file_url']
                            #if check_for_file(file_url, record):
                            #    print 'check for file'
			                #	continue
                            if file_url == False:
                                print 'record_id', record['_id']
                                continue
                            if file_url and 'backblazeb2' in file_url:
                                continue
                            new_url = get_new_url(user_email,file_url, record , _key, properties, bucket_files )
                            record['answers'][_key]['file_url'] = new_url
                            if new_url:
                                cur_col.update(
                                    {'_id':ObjectId(record['_id'])},
                                    {
                                        "$set": {
                                            'answers.' + _key: record['answers'][_key]
                                                 } })
                            else:
                				if record.has_key('folio'):
                					print 'check-folio=',record['folio']
                				else:
                					print 'check-_id=',record['_id']

                    elif isinstance(record['answers'][_key], list):
                        new_group = []
                        for group in record['answers'][_key]:
                            if isinstance(group, dict):
                                for group_key in group.keys():
                                    if isinstance(group[group_key], dict) and 'file_url' in group[group_key]:
                                        new_url = None
                                        file_url = group[group_key]['file_url']
    					                #if check_for_file(file_url, record):
                                    	#	continue
                                        # Change to absolute path
                                        if file_url and 'backblazeb2' in file_url:
                                            continue
                                        new_url = get_new_url(user_email,file_url, record , _key, properties, bucket_files )
                                        if new_url:
                                            group[group_key]['file_url'] = new_url

                                new_group.append(group)
                        cur_col.update(
                                    {'_id':ObjectId(record['_id'])},
                                    {
                                        "$set": {
                                            "answers." + _key: new_group
                                        }
                                    } )
            cur_db.client.close()
PIC.close()
LOST_PICS.close()
print 'records_with_errors=', records_with_errors
print 'dbs_with_errors=', databases_with_errors
