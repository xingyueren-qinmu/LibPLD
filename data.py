from enum import Enum, unique
from dataclasses import dataclass
from typing import List, Dict, IO
import os
import json
import geoip2.database

reader = geoip2.database.Reader(r'GeoLite2-City.mmdb')


# 找最长子串
def find_longest_substr(s1: str, s2: str):
    m = [[0 for i in range(len(s2) + 1)] for j in range(len(s1) + 1)]  # 生成0矩阵，为方便后续计算，比字符串长度多了一列
    # mmax=0   #最长匹配的长度
    p = 0  # 最长匹配对应在s1中的最后一位
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i] == s2[j]:
                m[i + 1][j + 1] = m[i][j] + 1
                if m[i + 1][j + 1] > mmax:
                    mmax = m[i + 1][j + 1]
                    p = i + 1
    return s1[p - mmax:p], mmax


class Config:
    class Msg:
        INIT = '初始化'
        ERROR = '错误'
        NONE = '无任务下发'
        GUOCE = '国测任务'
        WORKING = '设备已在工作中'

    class Path:
        LIBRADAR = ''
        LIBPECKER = ''
        DAE_RESULT = ''

    class Task:
        WAITING = 'WQ'
        PERFORMING = "PQ"
        DONE = 'DONE'

    class Codes:
        TASK_CODE_INIT = 0
        TASK_CODE_GUOCE = 10
        TASK_CODE_NONE = 1
        TASK_CODE_WORKING = 9
        TASK_STATUS_WAITING = 0
        TASK_STATUS_PERFORMING = 1
        TASK_STATUS_INQUEUE = 2
        TASK_STATUS_DONE = 3
        DEVICE_STATUS_INIT = -1
        DEVICE_STATUS_IDLE = 1
        DEVICE_STATUS_WORKING = 2
        DEVICE_STATUS_PAUSE = 3
        DAE_RET_SUCCEED = 100
        DAE_RET_FAILED = 200

    class PATH:
        LIBRADAR_RESULT = '/data/zhangqinyao/libradar/'
        UNPACK = 'frida_unpack_results/'
        TASK_TMP_RESULT = 'task_tmp_results/'

    class Api:
        NET_BEHAVIORS = {'网络通信', 'okhttp请求', 'okhttp响应'}
        CRYPTO_BEHAVIORS = {'加解密'}
        NORMAL_API_LIST = 'normal_api_list'
        NET_API_LIST = 'net_api_list'

    WRAPPERS = {'梆梆加固', '360加固', '通付盾加固', '网秦加固', '腾讯加固', '爱加密加固', '娜迦加固', '阿里聚安全加固',
                '百度加固', '网易易盾加固', 'APKProtect加固', '几维安全', '顶像科技', '盛大', '瑞星'}
    SENSITIVE_WORDS = {
        '设备信息': {'did', 'device_id', 'deviceid', 'device', 'brand', 'device', 'device_name', 'devicename', 'dbrand',
                 'device_brand', 'devicebrand', 'dname', 'ua', 'user-agent', 'agent', 'useragent'},
        '设备识别号': {'imei', 'sn', 'meid', 'guid', 'androidid', 'aid', 'android_id'},
        'MAC': {'mac'},
        '地理位置': {'loc', 'location', 'city', 'country', 'locationcity', 'current_location', 'current_city', 'city_id',
                 'coordinate', 'coor', 'coo', 'lat', 'lng'},
        '网络状态': {'ssid', 'bssid', 'operator', 'yunyingshang'},
        '短信': {'sms'},
        '日历': {'clander'}
    }

    SENSITIVE_BEHAVIORS = {
        '设备信息': '获取设备ID',
        '隐私信息': ''
    }
    # {'获取账户信息', '开始录音', '拍摄照片', '拍摄视频', '本机数据库查询', '本机数据库添加',
    #  '本机数据库删除', '本机数据库修改', '网络通信', '获取地理位置', '开始录音', '结束录音', '获取MAC地址',
    #  '获取WIFI IP', '获取Wifi SSID', '获取Wifi BSSID', '获取移动网络IP地址', 'Socket请求', 'Socket响应',
    #  'okhttp请求', 'okhttp响应', '获取本机安装应用', '获取传感器信息', '获取Android ID', '发送信息',
    #  '读取短信', '获取本机号码', '监听手机信息', '获取设备ID', '获取Sim卡MSI', '获取基站位置信息',
    #  '获取系统ID', '获取网络服务种类', '获取基站ID', '获取GSM原件ID', '获取地理位置', '获取运营商'}


@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class ApiResult:
    xrefFrom: List[str]
    className: str
    methodName: str
    permission: List[str]
    analysisinfo: List[Dict]
    analysisresult: int


@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class RequestResult:
    url: str
    code: str
    host: str
    beian: str
    desip: str
    method: str
    desaddr: str
    desport: str
    beiannum: str
    clientip: str
    protocol: str
    data_size: int
    timestamp: str
    desareacode: str
    descouncode: str
    request_raw: str
    analysisinfo: List[Dict]
    request_size: int
    response_raw: str
    response_size: int
    analysisresult: int
    plaintext: List[str]
    encoded_request_raw: str


@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class SDKResult:
    sdk_name: str
    sdk_version: str
    sdk_type: str
    sdk_pkgname: str
    sdk_version: str
    sdk_type: str
    deve: str
    sdkurl: str
    info: str


# 国测要的结果格式
@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class LibPLDResult:
    app_name: str
    app_md5: str
    sdk_info: SDKResult
    applied_range: str
    update: str
    back_url: str
    about_url: str
    activity: List[str]
    service: List[str]
    receiver: List[str]
    provider: List[str]
    permission: List[str]
    vulresult: str
    vulinfo: List[str]
    detectionlist: List[str]
    policyresult: str
    policyinfo: str
    departresult: str
    detail: List[str]
    descouncode: str
    desaddr: str
    apidata: [ApiResult]
    requestdata: []


class TmpResult:
    class Api:
        behavior: str
        method: str
        args: dict
        attrs: dict
        values: set
        xref: List[str]

        def __repr__(self):
            return '%r' % self.behavior

        def __init__(self, behavior, method, xref, **kwargs):
            self.behavior = behavior
            self.method = method
            self.values = kwargs.get('values')
            self.xref = xref
            args = kwargs.get('args')
            attrs = kwargs.get('attrs')

    lib_apis: Dict[str, Dict[str, List[Api]]]
    crypto_apis: List[Api]
    lib_net: Dict[str, List[RequestResult]]
    net_list: List[RequestResult]

    def __init__(self, task: Dict):
        dir = task['result_dir']
        libradar_file = os.path.join(dir, 'libradar.txt')
        libpecker_file = os.path.join(dir, 'libpecker.txt')
        request_file = os.path.join(dir, 'netmonitor_request.json')
        response_file = os.path.join(dir, 'netmonitor_response.json')
        api_file = os.path.join(dir, 'apimonitor.json')
        self.parse_net_result()

    def combine_lib_net(self):
        for lib in self.lib_apis.keys():
            for net_api in self.lib_apis[lib].get(Config.Api.NET_API_LIST):
                for net_info in self.net_list:
                    if net_info.host in net_api.args.get('url'):
                        if self.lib_net.get(lib) is None:
                            self.lib_net[lib] = []
                        self.lib_net[lib].append(net_info)

    def analyze(self):
        for lib in self.lib_apis.keys():
            # 先获得请求中的明文
            for api in self.crypto_apis:
                plaintext, ciphertext = api.args.get('input'), api.attrs.get('output')
                if api.attrs.get('opmode') == 'Decrypt':
                    plaintext, ciphertext = ciphertext, plaintext
                for req in self.lib_net[lib]:
                    if ciphertext in req.request_raw:
                        req.plaintext.append(plaintext)
            # 每个库的每个api的每个数据（args、relatedAttrs）
            for api in self.lib_apis[lib][Config.Api.NORMAL_API_LIST]:
                for v in api.values:
                    for net in self.lib_net[lib]:
                        net: RequestResult
                        if find_longest_substr(net.url, v)[1] > 4 or find_longest_substr(net.request_raw, v)[1] > 4:
                            net.analysisresult = 1
                            net.analysisinfo.append({api.behavior: v})

    def parse_net_result(self, request_file: str, response_file: str):
        global reader
        requests: Dict = json.load(open(request_file, 'r'))
        responses: Dict = json.load(open(response_file, 'r'))
        res = []
        for key in requests.keys():
            req: Dict = requests[key]

            res = responses.get(key)
            response_raw, response_size = '', 0
            if res is not None:
                response_raw = res.get('response_raw')
                response_size = res.get('response_size')
            geoip_response = reader.city(req.get('desip'))
            res.append(RequestResult(
                url=req.get('url'),
                code=req.get('code'),
                host=req.get('host'),
                desip=req.get('desip'),
                method=req.get('method'),

                desaddr=(str(geoip_response.country.name) +
                         str(geoip_response.subdivisions.most_specific.name) +
                         str(geoip_response.city.name)),
                # 目标地区编码和国家编码，经查，好像并没有所谓地区编码和国家编码这样的概念，有可能指的是电话代码
                # 但是geoip提供了geoname_id这个属性，因此先拿来使用
                desareacode=str(geoip_response.subdivisions.most_specific.geoname_id),
                descouncode=str(geoip_response.country.geoname_id),
                desport=req.get('desport'),
                beian='',
                beiannum='',
                data_size=req.get('content_length'),
                timestamp=req.get(''),
                request_raw=req.get('request_raw'),
                analysisinfo=[],
                request_size=req.get('request_size'),
                clientip='',
                protocol='',
                analysisresult=0,
                response_raw=response_raw,
                response_size=response_size,
                plaintext=[]
            ))
        self.net_list = res

    # 从文件读取api结果，转为API对象
    def parse_api_result(self, api_file: str, libs: List[str], pkgname: str):

        def get_lib_pkgname(cls: str, libs: List[str]) -> str:
            tmp = []
            for l in libs:
                if l in cls:
                    tmp.append(l)
                # elif not l.startswith(pkgname):
                #     tmp.append(l)
            if len(tmp) > 0:
                res = tmp[0]
                if len(tmp) > 1:
                    for l in tmp:
                        if len(l) > len(res):
                            res = l
                return res
            else:
                return cls

        j: Dict = json.load(open(api_file, 'r'))
        self.crypto_apis = []
        self.lib_apis = dict()
        for key in j.keys():
            e = j[key]
            lib = get_lib_pkgname(e['callingClass'], libs)
            if lib == e['callingClass']:
                continue
            if lib not in self.lib_apis.keys():
                tmp = self.lib_apis[lib] = dict()
                tmp[Config.Api.NORMAL_API_LIST] = []
                tmp[Config.Api.NET_API_LIST] = []
            tmp = self.lib_apis[lib][Config.Api.NORMAL_API_LIST]
            try:
                behavior = e['behavior']
                method = e['methodClass'] + '.' + e['method']
            except Exception:
                continue
            # 若是网络或加解密行为，记录在单独的列表中
            if behavior in Config.Api.NET_BEHAVIORS:
                tmp = self.lib_apis[lib][Config.Api.NET_API_LIST]
            elif behavior in Config.Api.CRYPTO_BEHAVIORS:
                tmp = self.crypto_apis
            # get方法可获得None返回，['x']遇到错误key会报错
            args: dict = e.get('methodArgs')
            attrs: dict = e.get('relatedAttrs')
            values = set()
            if args:
                for key in args.keys():
                    values.add(args[key])
            xref: List[str]
            if attrs:
                for attr in attrs.keys():
                    if attr == 'xrefFrom':
                        xref = attrs[attr]
                    else:
                        values.add(attrs[attr])
                attrs.pop('xrefFrom')

            tmp.append(TmpResult.Api(
                behavior, method, xref, values=values, args=args, attrs=attrs
            ))
            # if tmp is self.lib_apis[lib][Config.Api.CRYPTO_API_LIST]:
            #     self.lib_apis[lib][Config.Api.NORMAL_API_LIST].append(tmp[len(tmp) - 1])
