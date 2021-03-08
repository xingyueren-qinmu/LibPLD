import mitmproxy.http
from typing import Tuple, Dict


def get_plaintext_raw(req: mitmproxy.http.HTTPRequest, res: mitmproxy.http.HTTPResponse):
    from mitmproxy.contentviews.auto import ViewAuto
    ct, lines = ViewAuto()(res.get_content(), headers=req.headers)
    urlencoded_form = req.urlencoded_form
    req_content = req.get_content()
    raw = dict()
    content = [line for line in lines]
    if ct == 'Hex':
        if urlencoded_form:
            pass
    elif ct == 'No content':
        pass
    elif ct == 'XML' or ct == 'HTML':
        pass
    elif ct in ["image/png", "image/jpeg", "image/gif", "image/vnd.microsoft.icon", "image/x-icon", "image/webp"]:
        pass
    elif ct == 'Query':
        pass


class FlowCapture:

    def __init__(self):
        pass

    def response(self, flow: mitmproxy.http.HTTPFlow):
        import socket
        import geoip2.database


        req = flow.request
        res = flow.response
        if 'amap' in req.pretty_url:
            return
        print('-------------------')
        print(req.pretty_url)
        # Todo 根据 autoview 结果[0] 判断plaintext是否存在，是什么类型。
        print(req.urlencoded_form)
        # if 'content-type' in req.headers:
        #
        #     print(ct)
        #     from mitmproxy.contentviews import content_types_map
        #     if ct in content_types_map:
        #         print(content_types_map[ct][0][0])
        # else:
        #     print('header', req.headers)
        # try:
        #
        #     print('query', req.query)
        # except Exception as e:
        #     print(e)
        print('-------------------')

        # 这里是使用socket来借域名查IP
        # 注意：addr[0][4]返回的是所有符合的IP地址的列表，这里是选取了下标为0的一项
        addr = socket.getaddrinfo(req.host, 'http')
        desip = addr[0][4][0]
        # 用geolite数据库初始化reader
        reader = geoip2.database.Reader(r'GeoLite2-City.mmdb')
        # 输入desip之后，所有待获取的信息都由geoip_response获得，见下
        geoip_response = reader.city(desip)


addons = [FlowCapture()]