import shutil
import os
from main import mutex, tasks
from typing import List, Dict, Tuple
from subprocess import Popen, PIPE, call
from wrapper_detector import wd
from frida_unpack.frida_unpack import frida_unpack_main
from androguard.core.bytecodes.apk import APK
from data import Config,  find_longest_substr


# 脱壳
def unpack(apk_path: str) -> Dict:
    p = Popen('adb install -r %s' % apk_path, shell=True, stdout=PIPE)
    result = dict()
    if not p.wait() == 0:
        return {'install': False}
    result['install'] = 0
    pkgname = APK(apk_path).get_package()
    p = Popen('adb shell', stdin=PIPE, shell=True)
    p.communicate(bytes('su\nmagiskhide -add %s' % pkgname))
    result['magiskhide'] = p.wait()
    frida_unpack_main(pkgname)
    p = Popen('adb shell', stdin=PIPE, shell=True)
    p.communicate(
        bytes("su\nrm /data/data/%s/lib\ncp -r /data/data/%s/ /mnt/sdcard/" % (pkgname, pkgname), encoding="utf-8"))
    result['rmcp'] = p.wait()
    result['pull'] = call("adb pull /mnt/sdcard/%s/ %s" % (pkgname, Config.PATH.UNPACK), shell=True, stdout=PIPE)
    result['stop'] = call("adb shell am force-stop %s" % pkgname, shell=True, stdout=PIPE)
    result['uninstall'] = call("adb uninstall %s" % pkgname, shell=True, stdout=PIPE)
    dex_dir = os.path.join(Config.PATH.UNPACK, pkgname)
    dexes = []
    for f in os.listdir(Config.PATH.UNPACK):
        d = os.path.join(dex_dir, f)
        if f.endswith('.dex'):
            dexes.append(d)
        else:
            if os.path.isdir(d):
                shutil.rmtree(d)
            else:
                os.remove(d)
    result['dexes'] = dexes
    return result


# 执行静态分析
def static_analyze(task_id: str):
    global cursor, lib_result
    task = tasks[Config.Task.PERFORMING][task_id]
    apk_path = task.get('apk_path')
    apk_pkgname = APK(apk_path).get_package()
    libradar_result = []
    if wd.detect(apk_path) in Config.WRAPPERS:
        r = unpack(apk_path)
        if r.get('dexes') is not None:
            dexes = r.get('dexes')
            for dex in dexes:
                libradar_result.append(libradar(dex))
        else:
            libradar_result = libradar(task['id'], apk_path, apk_pkgname)
    else:
        libradar_result = libradar(task['id'], apk_path, apk_pkgname)
    result_dir = os.path.join(Config.PATH.TASK_TMP_RESULT, task.get('id'))
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    with open(os.path.join(result_dir, 'libradar.txt'), 'w') as f:
        f.writelines(libradar_result)
    '''
        libradar结果 pkg1\npkg2\npkg3\n
        libpecker结果: {pkg1:{lib1:{v1:s, v2:s}, lib2:{v1:s, v2:s}}, pkg2:{}, ...}
    '''
    lib_list = []
    for lib in libradar_result:
        cursor.execute("SELECT * FROM　sdk_info WHERE pkgname=%s", [lib])
        res = cursor.fetchall()
        if len(res) == 0:
            # Todo 如果查不到咋整
            pass
        elif len(res) > 1:
            # Todo 查到很多咋整
            pass
        else:
            lib_list.append(res[0])
    lib_result:Dict = libpecker(libradar_result)
    with open(os.path.join(result_dir, 'libpecker.txt'), 'w') as f:
        f.write(str(lib_result))
    mutex.acquire()
    task['result_dir'] = result_dir
    task['static_done'] = True
    if task['dae_done']:
        tasks[Config.Task.PERFORMING].pop(task_id)
        tasks[Config.Task.DONE].put(task)
    mutex.release()


# 使用 Libradar 识别 sdk
def libradar(id: str, apk_path: str, apk_pkgname: str) -> List:
    p = Popen(['python3', Config.PATH.LIBRADAR_RESULT + 'test.py', apk_path],
              shell=True, stdout=PIPE, cwd=Config.PATH.LIBRADAR_RESULT)
    pkgs: List[str] = []
    res: List[str] = []
    tmp = pkgs
    apk_pkgname = apk_pkgname.replace('.', '/')
    while p.poll() is None:
        line = str(p.stdout.readline())
        if line.startswith('Dividing-line'):
            tmp = res
            continue
        # 排除所有应用包名
        if apk_pkgname in line:
            continue
        tmp.append(line)
    # 处理libradar结果
    res = list(filter(filter_libradar_result, res))
    true_libs = []
    i = 0
    while i < len(res):
        (pkg1, lib1, s1) = res[i].split(' ')
        true_libs.append((pkg1, lib1, s1))
        if i == len(res) - 1:
            true_libs.append((pkg1, lib1, s1))
            break
        for j in range(i + 1, len(res)):
            (pkg2, lib2, s2) = res[j].split(' ')
            if lib1 in lib2:
                if s2 == '1.0':
                    continue
                elif s2 == s1:
                    true_libs.pop(len(true_libs) - 1)
                elif lib2.count('/') >= 3 and lib1.count('/') >= 3:
                    continue
            i = j
            break
    true_libs = [l[1].replace('/', '.') for l in true_libs]
    # 获取所有包名
    pkgs = set()
    for line in pkgs:
        line = line[1:]
        if line.startswith(apk_pkgname):
            continue
        if not line.endswith(';'):
            if not (line.startswith('android/') or line.startswith('google/android/') or line.startswith('kotlin') or line.startswith('androidx/')):
                pkgs.add(line)
    pkgs = list(pkgs)
    pkgs.sort()
    tree = dict()
    for line in pkgs:
        line = line.split('/')
        tmp = tree
        for pkg in line:
            if tmp.get(pkg) is None:
                tmp[pkg] = dict()
            tmp = tmp.get(pkg)
    pkgs = set()
    for key1 in tree.keys():
        n1 = tree[key1]
        for key2 in n1.keys():
            s = "%s.%s" % (key1, key2)
            n2 = n1[key2]
            while len(n2.keys()) == 1:
                key3 = list(n2.keys())[0]
                s += '.' + key3
                n2 = n2[key3]
            pkgs.add(s)
    pkgs.union(set(true_libs))
    pkgs = list(pkgs)
    pkgs.sort()
    return pkgs


# 过滤libradar结果
def filter_libradar_result(line: str) -> bool:
    line = line.split(' ')
    if len(line) != 3:
        return False
    if line[0].startswith('Landroid/') or line[0].startswith('Lgoogle/android/') or line[0].startswith('kotlin'):
        return False
    if line[1].count('/') > 4:
        return False
    if line[0] != line[1]:
        # 混淆
        if len(line[1].split('/')[0]) <= 2 and len(line[0].split('/')[0]) > 2:
            return True
        else:
            s, l = find_longest_substr(line[0], line[1])
            if l <= 4 and not line[0].startswith(s):
                return False
    return True


# 使用 LibPecker 识别 sdk 版本
def libpecker(sdk_list: List[str]) -> Dict:
    return dict()