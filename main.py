import pymysql
import _thread
import time
import hashlib
import json
import os
from threading import Lock
from queue import Queue
from zipfile import ZipFile
from typing import Dict, IO, List
from flask import Flask, request, Response
from data import Config, TmpResult
from perform_task import static_analyze
from concurrent.futures import ThreadPoolExecutor


app = Flask(__name__)
mutex = Lock()
tasks = {Config.Task.WAITING: Queue(), Config.Task.PERFORMING: dict(), Config.Task.DONE: Queue()}
cursor = pymysql.connect("192.168.97.1", "zhangqinyao", "Zqy2019!@#", "AASL").cursor()
lib_result: Dict


# 获取任务
@app.route('/get_task', methods=['POST'])
def get_task():
    global tasks, cursor
    device_id = request.args.get('DeviceID')
    device_status = int(request.args.get('DeviceStatus'))
    engine_version = request.args.get('EngineVersion')
    waiting_q:Queue = tasks[Config.Task.WAITING]
    # 判断测试机状态，若为
    if device_status == Config.Codes.DEVICE_STATUS_IDLE:
        if not waiting_q.empty():
            task:Dict = waiting_q.get()
            cursor.execute("UPDATE guoce_task SET "
                           "status=%s, device_id=%s, engine_version=%s"
                           "WHERE id=%s", [Config.Codes.TASK_STATUS_PERFORMING, device_id, engine_version, task['id']])
            # Todo 各类id细化
            response_dict = {
                'ret_code': Config.Codes.TASK_CODE_GUOCE,
                'msg': Config.Msg.GUOCE,
                'task_apk_id': task.get('id'),
                'task_id': task.get('id'),
                'task_detail_id': task.get('id'),
                'task_desc': '',
                'task_name': '',
                'task_apk_sha256': hashlib.sha256(open(task.get('apk_path'), 'rb').read()).hexdigest(),
                'task_run_interval': '60'
            }
            mutex.acquire()
            tasks[Config.Task.PERFORMING][task['id']] = task
            mutex.release()
            static_analyze(task['id'])
            return json.dumps(response_dict)
        else:
            return json.dumps({'ret_code': Config.Codes.TASK_CODE_NONE, 'msg': Config.Msg.NONE})
    elif device_status == Config.Codes.DEVICE_STATUS_INIT:
        return json.dumps({'ret_code': Config.Codes.TASK_CODE_INIT, 'msg': Config.Msg.INIT})
    elif device_status == Config.Codes.DEVICE_STATUS_WORKING:
        return json.dumps({'ret_code': Config.Codes.TASK_CODE_WORKING, 'msg': Config.Msg.WORKING})


# 下载被测app
@app.route('/get_apk', methods=['POST'])
def get_apk():
    id = request.args.get('apk_id')
    file_path: str = tasks[Config.Task.PERFORMING].get(id).get('apk_path')

    def send_file():
        with open(file_path, 'rb') as apk_file:
            while 1:
                data = apk_file.read(20 * 1024 * 1024)  # 每次读取20M
                if not data:
                    break
                yield data

    response = Response(send_file(), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=%s' % file_path[file_path.rfind('/') + 1:]
    response.headers["Content-Length"] = os.path.getsize(file_path)
    return response


# 返回结果
@app.route('/upload_result', methods=['POST'])
def upload_result():
    ret_code = int(request.form.get('ret_code'))

    if ret_code == Config.Codes.DAE_RET_SUCCEED:
        ret_json = request.form.get('ret_json')
        file = request.files.get('file')

        api_file: IO[bytes]
        net_file: IO[bytes]
        # Todo 读取网络通信结果
        timestamp = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
        result_dir = os.path.join(Config.PATH.TASK_TMP_RESULT, json.loads(ret_json)['apk_id'])
        with ZipFile(file) as dae_zip:
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
            for f in dae_zip.namelist():
                if f.startswith('netmonitor'):
                    with open(os.path.join(result_dir, f.split('@')[0]), 'wb') as nf:
                        nf.write(dae_zip.read(f))
                if f.startswith('apimonitor'):
                    with open(os.path.join(result_dir, 'apimonitor.json'), 'wb') as nf:
                        nf.write(dae_zip.read(f))
        mutex.acquire()
        task: Dict = tasks[Config.Task.PERFORMING][ret_json['apk_id']]
        task['result_dir'] = result_dir
        task['dae_finish_time'] = timestamp
        task['dae_done'] = True
        if task['static_done']:
            tasks[Config.Task.DONE].put(task)
            tasks[Config.Task.PERFORMING].pop(task['id'])
        mutex.release()
        return Response(status=200)


# 获取任务列表
def query_task():
    global cursor
    while True:
        cursor.execute("SELECT * FROM guoce_task WHERE task_status=%s", [Config.Codes.TASK_STATUS_WAITING])
        rows = cursor.fetchall()
        for row in rows:
            tasks[Config.Task.WAITING].put(
                {'id': row[0],
                 'task_name': row[1],
                 'apk_path': row[2],
                 'dae_done': False,
                 'static_done': False,
                 'unpack_path': '',
                 'result_dir': '',
                 'static_finish_time': 0,
                 'dae_finish_time': 0,
                 'final_result': None
                 }
            )
            cursor.execute("UPDATE guoce_task SET status=%s WHERE id=%s", [Config.Codes.TASK_STATUS_INQUEUE, row[0]])
        time.sleep(5)


def analyse_results():
    while True:
        if not tasks[Config.Task.DONE].empty():
            task: Dict = tasks[Config.Task.DONE].get()
            dae_result = TmpResult(task)





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999)
    pool = ThreadPoolExecutor(5)
    mutex = Lock()
    pool.map(query_task, ())
    pool.map(analyse_results, ())
    # subprocess(命令行调用)
    # 直接调用mitmproxy
