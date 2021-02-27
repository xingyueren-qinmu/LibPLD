# 手机上没有除了magisk,xposed installer,TWRP,RE文件管理器,DAE,猎豹清理大师,openvpn的其他非系统应用
# 需要先在测试机上启动frida-server,并且在使用时关闭magisk hide
# python frida_unpack_script.py a.apk

import os
import time
import sys
from frida_unpack.frida_unpack import frida_unpack_main
import subprocess
import shutil

result_path = 'frida_unpack_results'

if __name__ == "__main__":
    apk_location = sys.argv[1]
    os.popen("adb install -r %s" %apk_location)
    time.sleep(5)



    frida_unpack_main(package_name)
    time.sleep(5)

    procId = subprocess.Popen('adb shell',stdin = subprocess.PIPE)
    procId.communicate(bytes("su\nrm /data/data/{}/lib\ncp -r /data/data/{}/ /mnt/sdcard/".format(package_name,package_name),encoding="utf-8"))
    time.sleep(5)

    # os.popen("mkdir F:\\作业及课件\\研1上\\tuoke\\frida_unpack_results\\{}".format(package_name))
    pull_result = os.popen("adb pull /mnt/sdcard/{}/ {}".format(package_name,result_path)).read()
    print (pull_result)
    os.popen("adb shell am force-stop %s" %package_name)
    time.sleep(8)
    os.popen("adb uninstall %s" %package_name)

    os.chdir(result_path+"/"+package_name)
    all_files = os.listdir()
    for each_file in all_files:
        if not each_file.endswith(".dex"):
            if os.path.isdir(each_file):
                shutil.rmtree(result_path+"/"+package_name+"/"+each_file)
            else:
                os.remove(result_path+"/"+package_name+"/"+each_file)


    # com.webank.wemoney
    # com.xiaomi.loan