# coding: utf-8

import os
import re
import platform
import zipfile
import sys
import getopt
from wrapper_detector import constant


class ApkProtection:
    def __init__(self, dit):
        self.apk_path = dit['apk_path']
        self.aapt_path = dit['aapt_path']
        self.xmltree = ''  # 通过aapt获取的manifest.xml
        self.wrapper_sdk = constant.NOWRAPPER
        self.lastError = ''
        self.appdit = {'wrapperSdk': '', 'last_error': ''}
        self.zipnamelist = []
        self.so_compile = {}
        self.app_compile = {}
        self.init()

    def init(self):
        so_feature = constant.SO_FEATURE
        app_feature = constant.APPLICATION_FEATURE
        # print(so_feature)
        for (key, value) in so_feature.items():
            self.so_compile[key] = re.compile(value, re.I)
        for (key, value) in app_feature.items():
            self.app_compile[key] = re.compile(value, re.I)

    # 读取APK文件名列表

    def getZipNameList(self, apk_path):
        self.lastError = ''
        if not os.path.isfile(apk_path):
            self.lastError = u'apk文件不存在'
            return False
        if not zipfile.is_zipfile(apk_path):
            self.lastError = u'非法的apk文件'
            return False
        try:
            zfobj = zipfile.ZipFile(apk_path)
            self.zipnamelist = zfobj.namelist()
            zfobj.close()
        except Exception as e:
            # print "%s" % e
            self.lastError = u'获取apk中文件列表异常'
            return False
        return True

    # 通过aapt获取的manifest.xml
    def getXmlInfo(self):
        xml_cmd = ''
        self.lastError = ''

        if 'Windows' in platform.system():
            xml_cmd = "%s d xmltree \"%s\" AndroidManifest.xml " % (
                self.aapt_path, self.apk_path)

        if 'Linux' in platform.system():
            xml_cmd = "%s d xmltree %s AndroidManifest.xml " % (
                self.aapt_path, self.apk_path)

        try:
            strxml = os.popen(xml_cmd)
            self.xmltree = strxml.read()
        except Exception as e:
            self.lastError = 'aapt get AndroidManifest.xml error'
            return False
        return True

    # 从xml中检测加壳信息
    def checkManifest(self):
        for (key, value) in self.app_compile.items():
            result = value.search(self.xmltree)
            if result:
                return key
        return constant.NOWRAPPER

    # 获取APK的加壳厂商

    def getWrapperSdk(self):
        self.lastError = ''
        manifest_result = self.checkManifest()
        # print(manifest_result)
        find = False
        so_result = constant.NOWRAPPER
        try:
            for fileName in self.zipnamelist:
                for (key, value) in self.so_compile.items():
                    result = value.search(fileName)
                    if result:
                        so_result = key
                        find = True
                        break
        except Exception as e:
            self.lastError = 'parser wrap lib error'
            return False
        if find:
            if manifest_result == so_result:
                self.wrapper_sdk = so_result
            elif manifest_result == constant.NOWRAPPER and so_result != constant.NOWRAPPER:
                self.wrapper_sdk = so_result
            elif manifest_result != so_result:
                self.wrapper_sdk = constant.RESULTSTRING + so_result
            else:
                self.wrapper_sdk = constant.NOWRAPPER
        else:
            if manifest_result == constant.NOWRAPPER:
                self.wrapper_sdk = manifest_result
            else:
                self.wrapper_sdk = constant.RESULTSTRING + manifest_result

    # 该函数最后调用，更新全局字典类型
    def getAppDit(self):
        self.appdit['last_error'] = self.lastError
        self.appdit['wrapper_sdk'] = self.wrapper_sdk

    def apkDetect(self):
        if not self.getXmlInfo():
            return
        if not self.getZipNameList(self.apk_path):
            return
        self.getWrapperSdk()

    def result(self):
        self.apkDetect()
        self.getAppDit()
        return self.appdit


def detect(dic: str) -> str:
    try:
        # opts, args = getopt.getopt(
        #     argv, "-h-i:-t:", ["help", "input=", "aapt="])
        # if len(opts) < 1:
        #     usage()
        #     print("\nToo few arguments!")
        #     sys.exit(2)
        # dic = {'apk_path': "", "aapt_path": ""}
        # if 'Linux' in platform.system():
        #     dic["aapt_path"] = "./tools/aapt"
        # if 'Windows' in platform.system():
        #     dic["aapt_path"] = "tools\\aapt.exe"
        # for opt, arg in opts:
        #     if opt in ("-h", "--help"):
        #         print(usage())
        #         sys.exit(2)
        #     elif opt in ("-i", "--input"):
        #         dic['apk_path'] = arg
        #     elif opt in ("-t", "--aapt"):
        #         dic["aapt_path"] = arg
        ad = ApkProtection(dic)
        result = ad.result()
        if result['last_error'] != '':
            return result['last_error']
        else:
            return result['wrapper_sdk']
    except Exception as e:
        print(e)
        return 'error'


def usage():
    banner = """
               _____  _  _______           _            _   _             
     /\   |  __ \| |/ /  __ \         | |          | | (_)            
    /  \  | |__) | ' /| |__) | __ ___ | |_ ___  ___| |_ _  ___  _ __  
   / /\ \ |  ___/|  < |  ___/ '__/ _ \| __/ _ \/ __| __| |/ _ \| '_ \ 
  / ____ \| |    | . \| |   | | | (_) | ||  __/ (__| |_| | (_) | | | |
 /_/____\_\_|    |_|\_\_|   |_|  \___/ \__\___|\___|\__|_|\___/|_| |_|

  / ____|                   | |                                       
 | (___   ___  __ _ _ __ ___| |__                                     
  \___ \ / _ \/ _` | '__/ __| '_ \                                    
  ____) |  __/ (_| | | | (__| | | |                                   
 |_____/ \___|\__,_|_|  \___|_| |_|
 """
    print(banner)
    print("\nUSAGE:\t" + sys.argv[0] + " -h")
    print("\t" + sys.argv[0] + " -i app.apk\n")
    print("\t-i, --input\t The target apk file.")
    print("\t-a, --aapt\t The aapt file path.")


if __name__ == "__main__":
    # detect(sys.argv[1:])
    pass
