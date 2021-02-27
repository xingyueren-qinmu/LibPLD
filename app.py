# -*- coding=utf-8 -*-
import datetime

import pymysql
from DBUtils.PooledDB import PooledDB
from flask import Flask, request, Response, send_file
from flask import make_response
from werkzeug.utils import secure_filename
import urllib.parse
import pymongo
from gridfs import *
import redis
import json
import os

import hashlib
import numpy

POOL = PooledDB(
    creator=pymysql,
    maxconnections=None,
    mincached=1,
    maxcached=20,
    host='192.168.97.1',
    user='yinzhiying',
    password='Yzy2019!#',
    db='AASL'
)
# db = pymysql.connect(host='192.168.97.1',user='yinzhiying',password='Yzy2019!#',db='AASL')
# cursor = db.cursor()
# 未测试                       #滑动计数问题，不能只在最开始滑动
# 修改了request_apk，添加了一个if判断，优先测试baidunet的内容
# 修改了所有有resultpath的地方，修改如果测得是baidu里的app，结果放到baidunet结果里，但是可能最后几个app结果会偏差
separator = os.sep
# appPath = "C:\\Users\\13194\\Desktop\\app" #apk存放路径
# appPath = '/data/mount/apk20190521market/0521'
# baiduapppath = "/data/yinzhiying/baidunet"
# baiduresultpath = "/data/yinzhiying/baidunetresult"
# Path = "F:\\result" # 结果存放路径
Path = '/data/yinzhiying/result'
app = Flask(__name__)
redis_db = redis.Redis(host='192.168.97.7', port=6379, decode_responses=True, charset='UTF-8', db='1')  # 默认使用0数据库

config_mongo_host = "192.168.97.1"
config_mongo_port = 27017
config_mongo_db = "dynamicResult"
config_mongo_collection = "domainSystemresult"
config_mongo_encoding = "utf-8"
config_json_encoding = "utf-8"

client_mongo = pymongo.MongoClient('mongodb://yinzhiying:Yzy2019!@192.168.97.1:27017/')
mongo_db = client_mongo[config_mongo_db]  # 数据库
mongo_col = mongo_db[config_mongo_collection]  # 集合
Phonestatus = numpy.zeros(20)


@app.route('/')
def hello():
    print("hello")
    return "hello world!"


@app.route('/Test/status', methods=['POST'])
def upload_TestStatus():
    s = mongo_db['domainengineversion'].find().sort([('id', -1)]).limit(1)
    for i in s:
        engineversion = i['version']
    data = json.loads(request.get_data())
    filesha256 = data["Filesha256"]
    # print(filepath)
    status = data["Teststatus"]
    endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "Success":
        mongo_col.update_many({'filesha256': filesha256, 'engineversion': engineversion},
                              {"$set": {'status': status, 'endtime': endtime}})  # 修改
    else:
        mongo_col.delete_many({'filesha256': filesha256, 'engineversion': engineversion})
    rt = {"json": True}
    return Response(json.dumps(rt), mimetype='application/json')


@app.route('/Phone/phonestatus', methods=['POST', 'GET'])
def upload_PhoneStatus():
    data = json.loads(request.get_data())
    # phonename = "PIXEL1-1"
    phonename = data["phonestatus"]
    db = POOL.connection()
    cursor = db.cursor()
    sql = "update PhoneStatus set status =1 where phoneName = \"%s\" " % (phonename)
    print(sql)
    try:
        cursor.execute(sql)
        db.commit()
    except:
        # print("roll")
        db.rollback()
    cursor.close()
    db.close()
    rt = {"json": True}
    return Response(json.dumps(rt), mimetype='application/json')


@app.route('/upload/picture', methods=['POST'])
def upload_picture():
    screenpicture1 = request.files['filepicture1']
    picturename1 = secure_filename(screenpicture1.filename)
    screenpicture2 = request.files['filepicture2']
    picturename2 = secure_filename(screenpicture2.filename)
    screenpicturexml1 = request.files['xml1']
    xmlname1 = secure_filename(screenpicturexml1.filename)
    screenpicturexml2 = request.files['xml2']
    xmlname2 = secure_filename(screenpicturexml2.filename)
    filesha256 = request.form['filesha256']
    # if redis_db.llen('filelist_baidunet')>0:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    #     # resultPath = baiduresultpath + separator+  today + separator + filesha256
    resultPath = Path + separator + today + separator + filesha256
    # else:
    #     resultPath=Path + separator + filesha256
    ispath(resultPath)
    picturePath = resultPath + separator + "Picture"
    ispath(picturePath)
    screenpicture1.save(os.path.join(picturePath, picturename1))
    screenpicture2.save(os.path.join(picturePath, picturename2))
    screenpicturexml1.save(os.path.join(picturePath, xmlname1))
    screenpicturexml2.save(os.path.join(picturePath, xmlname2))
    # mongo存截图
    datatmp1 = open(picturePath + separator + picturename1, 'rb')
    datatmp2 = open(picturePath + separator + picturename2, 'rb')
    datatmp3 = open(picturePath + separator + xmlname1, 'rb')
    datatmp4 = open(picturePath + separator + xmlname2, 'rb')
    imgput = GridFS(mongo_db)
    imgput.put(datatmp1, content_type=picturename1.split('.')[len(picturename1.split('.')) - 1], filename=picturename1)
    imgput.put(datatmp2, content_type=picturename2.split('.')[len(picturename2.split('.')) - 1], filename=picturename2)
    imgput.put(datatmp3, content_type=xmlname1.split('.')[len(xmlname1.split('.')) - 1], filename=xmlname1)
    imgput.put(datatmp4, content_type=xmlname2.split('.')[len(xmlname2.split('.')) - 1], filename=xmlname2)
    datatmp1.close()
    datatmp2.close()
    datatmp3.close()
    datatmp4.close()
    rt = {"json": True}
    return Response(json.dumps(rt), mimetype='application/json')


@app.route('/upload/pcap', methods=['POST'])
def upload_pcap():
    f = request.files['filepcap']
    filename1 = secure_filename(f.filename)
    filesha256 = request.form['filesha256']
    # if redis_db.llen('filelist_baidunet') > 0:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # resultPath = baiduresultpath + separator + today + separator + filesha256
    resultPath = Path + separator + today + separator + filesha256
    # else:
    #     resultPath = Path + separator + filesha256
    ispath(resultPath)
    f.save(os.path.join(resultPath, filename1))
    rt = {"json": True}
    return Response(json.dumps(rt), mimetype='application/json')


@app.route('/upload/txt', methods=['POST'])
def upload_txt():
    f = request.files['filetxt']
    filename1 = secure_filename(f.filename)
    Filesha256 = request.form['Filesha256']
    # if redis_db.llen('filelist_baidunet') > 0:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    resultPath = Path + separator + today + separator + Filesha256
    # resultPath = baiduresultpath + separator + today + separator + Filesha256
    # else:
    #     resultPath = Path + separator + Filesha256
    ispath(resultPath)
    f.save(os.path.join(resultPath, filename1))
    rt = {"json": True}
    return Response(json.dumps(rt), mimetype='application/json')


@app.route('/deal', methods=['POST'])
def deal():
    from deal_result import main
    data = json.loads(request.get_data())
    filename = data['filename']
    PackageName = data['PackageName']
    filemd5 = data['filemd5']
    filesha256 = data['filesha256']
    appname = urllib.parse.unquote(data['appname'])
    versionname = data['versionname']
    PhoneName = data["PhoneNumber"]
    StartTime = data["StartTime"]
    filerealpath = data["FilePath"]
    s = mongo_db['domainengineversion'].find().sort([('id', -1)]).limit(1)
    for i in s:
        engineversion = i['version']
    # mongo_col.update({'filesha256': filesha256,'engineversion':engineversion},{"$set": {'packagename':PackageName,'filemd5':filemd5,'appname':appname,'versionname':versionname,
    #                       'filename':'',                                                              'PhoneNumber':PhoneName,'apppath':filerealpath,'resultfilepath':Path}})
    JsonResult = {'filename': '', 'packagename': '', 'filemd5': '', 'filesha256': '', 'appname': '',
                  'versionname': '', 'engineversion': '',
                  'result': {'domain': [], 'dns': [], 'ssl': [], 'ip': [], 'portinfo': ''}, 'status': '', 'endtime': '',
                  'starttime': ''}
    JsonResult['filename'] = filename
    JsonResult['packagename'] = PackageName
    JsonResult['filemd5'] = filemd5
    JsonResult['filesha256'] = filesha256
    JsonResult['appname'] = appname
    JsonResult['versionname'] = versionname
    # JsonResult['PhoneNumber'] = PhoneName
    JsonResult['starttime'] = StartTime
    JsonResult['apppath'] = filerealpath
    JsonResult['resultfilepath'] = Path
    JsonResult['engineversion'] = engineversion

    # if redis_db.llen('filelist_baidunet') > 0:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # resultPath = baiduresultpath + separator + today + separator + filesha256
    resultPath = Path + separator + today + separator + filesha256
    # else:
    #     resultPath = Path + separator + filesha256
    ispath(resultPath)
    flag = main.mainFun(resultPath, PackageName, JsonResult, filesha256)
    endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    JsonResult['endtime'] = endtime
    resultJson = open(resultPath + separator + filesha256 + ".json", 'w', encoding='utf-8')
    JsonData = json.dumps(JsonResult, ensure_ascii=False)
    resultJson.write(JsonData)
    mongo_col.update({'filesha256': filesha256, 'engineversion': engineversion}, {"$set": JsonResult})
    resultJson.close()
    jsons = {"json": flag}
    return Response(json.dumps(jsons), mimetype='application/json')


# def get_task():
#     redis_db.delete('dynamictask')
#     sql_task = 'select task_id,engine_type from task_engine where engine_status =1'
#     cursor.execute(sql_task)
#     task_ids = cursor.fetchall()
#     print(task_ids)
#     sql_detail = 'select apk_id from task_detail where task_id = '
#     sql_apks = 'select apk_file_path from sample_apk where id = '
#     for i in range(0,len(task_ids)):
#         if task_ids[i][1] != 1:
#             continue
#         sql_det = sql_detail + str(task_ids[i][0])
#         print(str(task_ids[i][0]))
#         cursor.execute(sql_det)
#         tasks = cursor.fetchmany(5)#改为fetchall()
#         print(tasks)
#         for j in range(0,len(tasks)):
#             sql_apk = sql_apks+ str(tasks[j][0])
#             cursor.execute(sql_apk)
#             taskredis = cursor.fetchone()
#             print(taskredis)
#             if '.apk' in taskredis[0] or '.APK' in taskredis[0]:
#                 d = {"filepath_name": taskredis[0]}
#                 jsn = json.dumps(d)
#                 redis_db.rpush("task", jsn)
# @app.route('/request/apk', methods=['POST'])
# def request_apk():
#     starttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     message = json.loads(request.get_data())
#     sign = message["apk"]
#     content = False
#     s = mongo_db['domainengineversion'].find().sort([('id', -1)]).limit(1)
#     for z in s:
#         engineversion = z['version']
#     keys = redis_db.keys()#获取redis里的所有键
#     # if len(keys) == 0:
#     #     import redis_deal
#     #     redis_deal.get_longtask()
#     if len(keys)!=0:
#         filejson = json.loads(redis_db.lpop(keys[0]))
#         filepath = filejson["filepath_name"]
#         filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()#修改无需目录
#         a = mongo_col.find_one({'filesha256': filesha256,'engineversion':engineversion})  # 查询结果表中所有已测过的任务的sha256
#         while a != None and redis_db.llen(keys[0]) != 0:
#             # print(filesha256)
#             filejson = json.loads(redis_db.lpop(keys[0]))
#             filepath = filejson["filepath_name"]
#             filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
#             # Tested = []
#             a = mongo_col.find_one({'filesha256': filesha256,'engineversion':engineversion})  # 查询结果表中所有已测过的任务的sha256
#         response = make_response(send_file(filepath, as_attachment=True))
#     # elif redis_db.llen("task1000") != 0:
#     #     print('1')
#     #     filejson = json.loads(redis_db.lpop("task1000"))
#     #     filename = filejson["filename"]
#     #     Tested = []
#     #     filesha256 = hashlib.sha256(open(appPath+separator+filename, 'rb').read()).hexdigest()
#     #     a = mongo_col.find_one({'filesha256': filesha256,'engineversion':engineversion})  # 查询结果表中所有已测过的任务的sha256
#     #     while a != None:
#     #         print(filesha256)
#     #         filejson = json.loads(redis_db.lpop("task1000"))
#     #         filename = filejson["filename"]
#     #         filesha256 = hashlib.sha256(open(appPath + separator + filename, 'rb').read()).hexdigest()
#     #         a = mongo_col.find_one({'filesha256': filesha256,'engineversion':engineversion})
#     #     response = make_response(send_from_directory(appPath, filename, as_attachment=True))
#     else:
#         # import redis_deal
#         # redis_deal.get_longtask()
#         filepath = os.getcwd()+separator+"empty.txt"
#         if not os.path.exists(filepath) or  not os.path.isfile(filepath):
#             os.mknod(filepath)
#         print("emptyfile ")
#         response = make_response(send_file(filepath, as_attachment=True))
#     if sign is True and content is True:
#         response.headers["Content-Disposition"] = "{}".format(urllib.parse.quote_plus(filepath.split('/')[len(filepath.split('/'))-1]))#传回真实文件名
#         response.headers["StartTime"] = "{}".format(urllib.parse.quote_plus(starttime))  # 传回真实文件名
#     else:
#         response.headers["Content-Disposition"] = "{}".format(urllib.parse.quote_plus(filepath.split('/')[len(filepath.split('/'))-1]))
#         response.headers["StartTime"] = "{}".format(urllib.parse.quote_plus(starttime))  # 传回真实文件名
#     return response

@app.route('/request/apk', methods=['POST'])
def request_apk():
    starttime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = json.loads(request.get_data())
    sign = message["apk"]
    Phone = message["PhoneName"]
    print(Phone)
    content = False
    s = mongo_db['domainengineversion'].find().sort([('id', -1)]).limit(1)
    for z in s:
        engineversion = z['version']
    # keys = redis_db.keys()
    # while len(keys) != 0:
    #     key = keys[0]
    if redis_db.llen('filelist_baidunet') != 0:
        filejson = json.loads(redis_db.lpop("filelist_baidunet"))
        filepath = filejson["filename"]
        print(filepath)
        filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()  # 修改无需目录
        a = mongo_col.find_one({'filesha256': filesha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
        while a != None:
            print(filesha256)
            filejson = json.loads(redis_db.lpop("filelist_baidunet"))
            filepath = filejson["filename"]
            filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
            # Tested = []
            a = mongo_col.find_one({'filesha256': filesha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
        #########先插入数据
        JsonResult = {'filename': '', 'packagename': '', 'filemd5': '', 'filesha256': '', 'appname': '',
                      'versionname': '', 'engineversion': '',
                      'result': {'domain': [], 'dns': [], 'ssl': [], 'ip': [], 'portinfo': ''}, 'status': '',
                      'PhoneNumber': '', 'endtime': '', 'starttime': ''}
        JsonResult['filesha256'] = filesha256
        JsonResult['filename'] = filepath
        JsonResult['starttime'] = starttime
        JsonResult['engineversion'] = engineversion
        JsonResult['PhoneNumber'] = Phone
        mongo_col.insert_one(JsonResult)
        ######先插入数据
        response = make_response(send_file(filepath, as_attachment=True))
    elif redis_db.llen("task1000") != 0:
        print('1')
        filejson = json.loads(redis_db.lpop("task1000"))
        filepath = filejson["filename"]
        Tested = []
        filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
        a = mongo_col.find_one({'filesha256': filesha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
        while a != None:
            print(filesha256)
            filejson = json.loads(redis_db.lpop("task1000"))
            filepath = filejson["filename"]
            filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
            a = mongo_col.find_one({'filesha256': filesha256, 'engineversion': engineversion})
        JsonResult = {'filename': '', 'packagename': '', 'filemd5': '', 'filesha256': '', 'appname': '',
                      'versionname': '', 'engineversion': '',
                      'result': {'domain': [], 'dns': [], 'ssl': [], 'ip': [], 'portinfo': ''}, 'status': '',
                      'PhoneNumber': '', 'endtime': '', 'starttime': ''}
        JsonResult['filesha256'] = filesha256
        JsonResult['filename'] = filepath
        JsonResult['starttime'] = starttime
        JsonResult['engineversion'] = engineversion
        JsonResult['PhoneNumber'] = Phone
        mongo_col.insert_one(JsonResult)
        response = make_response(send_file(filepath, as_attachment=True))
    else:
        filepath = "/home/yinzhiying/empty.txt"
        if not os.path.isfile(filepath):
            f = open(filepath, "w+")
        print("emptyfile ")
        response = make_response(send_file(filepath, as_attachment=True))
    filedir, filename = os.path.split(filepath)
    print(filename)
    if sign is True and content is True:
        response.headers["Content-Disposition"] = "{}".format(urllib.parse.quote_plus(filename))  # 传回真实文件名
        response.headers["StartTime"] = "{}".format(urllib.parse.quote_plus(starttime))  # 传回开始检测时间
        response.headers["filepath"] = "{}".format(urllib.parse.quote_plus(filepath))  # 传回开始检测时间
    else:
        response.headers["Content-Disposition"] = "{}".format(urllib.parse.quote_plus(filename))
        response.headers["StartTime"] = "{}".format(urllib.parse.quote_plus(starttime))  # 传回开始检测时间
        response.headers["filepath"] = "{}".format(urllib.parse.quote_plus(filepath))  # 传回开始检测时间
    return response


# @app.route('',methods=['POST','GET'])


def ispath(file_dir):
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)


def del_file(path):
    for i in os.listdir(path):
        path_file = os.path.join(path, i)
        if os.path.isfile(path_file):
            os.remove(path_file)
        else:
            del_file(path_file)


# def file_name(file_dir):
#     filenames = []
#     redis_db.delete("task1000")
#     for root, dirs, files in os.walk(file_dir):
#         for file in files:
#             if file == ".DS_Store":
#                 continue
#             if file == "empty.txt":
#                 continue
#             if '.apk' in file or '.APK' in file:
#                 print(root)
#                 d = {"filename": root+os.sep+file}
#                 jsn = json.dumps(d)
#                 redis_db.rpush("task1000", jsn)
#     f = redis_db.lrange("task1000", 0, -1)
#     print(f)
#     # filejson = json.loads(redis_db.lpop("task1000"))
#     # filepath = filejson["filename"]
#     # Tested = []
#     # filesha256 = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
#     # print(filesha256)
#     if redis_db.llen("task1000") == 0:
#         return False
#     return True
#
# file_name( "C:\\Users\\13194\\Desktop\\app")
# def get_task():
#     message = json.loads(request.get_data())
#     devie_id = message["DeviceID"]
#     device_status = message["Status"]
#     version = mongodb["domainengineversion"].find().sort([('id', -1)]).limit(1)  # 引擎当前版本
#     for z in version:
#         engineversion = z['version']
#     ret_json = {  # 返回客户端数据
#         "ret_code": 0,
#         "msg": 1,
#         "task_id": 0,
#         "task_detail_id": 0,
#         "task_desc": "0",
#         "task_name": "0",
#         "task_run_interval": config.task_run_interval,
#         "task_apk_id": 0
#     }
#     json_result = dict(apk_id=None, apk_file_path='', packagename='', filemd5='', filesha256='', appname='',
#                        versionname='',
#                        engineversion='', result={'domain': [], 'dns': [], 'ssl': [], 'ip': [], 'portinfo': ''},
#                        status='', PhoneNumber='', endtime='', starttime='')
#     if device_status == 1:  # 手机处于空闲状态
#         if redisdb.llen("task_dict") == 0:
#          # 没有临时任务
#             if redisdb.llen("basic_task") != 0:
#                 task_json = json.loads(redisdb.lpop("basic_task"))
#                 task_sha256 = task_json["file_sha256"]
#                 retask = mongodb["domainSystemresult"].find_one(
#                     {'filesha256': task_sha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
#                 while retask is not None and redisdb.llen("basic_task") != 0:
#                     task_json = json.loads(redisdb.lpop("basic_task"))
#                     task_sha256 = task_json["file_sha256"]
#                     retask = mongodb["domainSystemresult"].find_one(
#                         {"filesha256": task_sha256, "engineversion": engineversion})  # 查询结果表中所有已测过的任务的sha256
#                 ret_json["task_apk_id"] = task_json["apk_id"]
#                 ret_json["ret_code"] = 2
#                 ret_json["msg"] = "基础任务"
#                 json_result["apk_id"] = task_json["apk_id"]
#                 json_result["apk_file_path"] = task_json["apk_file_path"]
#                 json_result['filesha256'] = task_sha256
#                 start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 任务开始时间
#                 json_result['starttime'] = start_time
#                 json_result['engineversion'] = engineversion
#                 json_result['PhoneNumber'] = devie_id
#                 mongodb["domainSystemresult"].insert(json_result)
#             else:
#                 ret_json["ret_code"] = 0
#                 ret_json["msg"] = "无任务"
#         else:  # 临时任务优先级处理
#             task_dict = json.loads(redisdb.lpop("task_dict"))
#             task_list = sorted(task_dict.items(), key=lambda x: x[1], reverse=True)
#             for i in range(0, len(task_list)):
#                 if redisdb.llen(task_list[i][0]) != 0:
#                     task_json = json.loads(redisdb.lpop(task_list[i][0]))
#                     task_sha256 = task_json["file_sha256"]
#                     retask = mongodb["domainSystemresult"].find_one(
#                         {'filesha256': task_sha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
#                     while retask is not None and redisdb.llen(task_list[i][0]) != 0:
#                         task_json = json.loads(redisdb.lpop(task_list[i][0]))
#                         task_sha256 = task_json["file_sha256"]
#                         retask = mongodb["domainSystemresult"].find_one(
#                             {'filesha256': task_sha256, 'engineversion': engineversion})  # 查询结果表中所有已测过的任务的sha256
#                     if retask is None:
#                         ret_json["ret_code"] = 1
#                         ret_json["msg"] = "普通任务"
#                         ret_json["task_apk_id"] = task_json["apk_id"]
#                         ret_json["task_id"] = task_json["task_id"]
#                         ret_json["task_detail_id"] = task_json["task_detail_id"]
#                         ret_json["task_desc"] = task_json["task_desc"]
#                         ret_json["task_name"] = task_json["task_name"]
#                         json_result["apk_id"] = task_json["apk_id"]
#                         json_result["apk_file_path"] = task_json["apk_file_path"]
#                         json_result['filesha256'] = task_sha256
#                         start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 任务开始时间
#                         json_result['starttime'] = start_time
#                         json_result['engineversion'] = engineversion
#                         json_result['PhoneNumber'] = devie_id
#                         mongodb["domainSystemresult"].insert(json_result)
#                         break
#     else:
#         ret_json["ret_code"] = -1
#         ret_json["msg"] = "错误"
#     return Response(json.dumps(ret_json), mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # debug是否需要去掉，, threaded=True默认threaded是True
