# coding: utf-8

# from db.white_list import WhiteList
from db.myredis import mget, mset
from functools import wraps
from flask import request
from config import *

import CloudFlare
import traceback
import requests
import hashlib
import boto3
import time
import json

# 屏蔽https告警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def handle_httpresponse(data, status=-1, other={}):
    '''
    处理返回结果
    :param data: 数据
    :param status: 返回状态 0(成功) -1(不成功)
    :param other: 其他需要加入的数据
    :return: json格式的数据
    '''
    return_dic = {'data': data, 'status': Return_Statua_Code.error}
    if status == 0:
        return_dic['status'] = Return_Statua_Code.ok
    if other:
        for i in other:
            return_dic[i] = other[i]
    return json.dumps(return_dic)


def create_token(uid):
    token = hashlib.sha1(os.urandom(24)).hexdigest()
    mset(token, uid, 60*60*48)
    return token


def get_uid():
    return mget(request.headers["token"])


# --------------------------------------------------------
# 装饰器
# --------------------------------------------------------
def is_login_zsq(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            uid = mget(request.headers["token"])
            if uid is not None:
                return func(*args, **kwargs)
            else:
                return handle_httpresponse('未登录!')
        except Exception as e:
            print(f'登录错误, 错误原因[{e}]!', 2, '登录错误')
            return handle_httpresponse('未登录!')
    return inner


def handle_api_zsq(api_path, method):
    # 处理http response装饰器
    def zsq(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if method == 'get':
                _ = f'{request.headers.get("X-Real-IP")} {method.upper()} => {api_path}{list(kwargs.values())[0]} : 【{request.args}】'
            else:
                _ = f'{request.headers.get("X-Real-IP")} {method.upper()} => {api_path} : ' \
                    f'【{request.args if method == "GET" else request.form if method == "POST" else request.data}】'
            print(_, 0, 'request', LogDefine.request_log_file.format(time.strftime("%Y-%m-%d", time.localtime())))
            try:
                resp = func(*args, **kwargs)
            except KeyError:
                # traceback.print_exc()
                resp = handle_httpresponse('参数错误!')
            except Exception as e:
                # traceback.print_exc()
                er = ";".join(traceback.format_exc().split("\n"))
                print(f'服务器错误, 错误原因 [{er}]!!!', 2, '服务器错误')
                resp = handle_httpresponse(f'服务器错误, 错误原因 [{e}]')
            return resp
        return inner
    return zsq


def my_requests(url, method, params=None, headers=None, need_json_resp=True,
                verify=False, need_json_params=False, need_proxies=False, proxies=None, need_content=False):
        '''
        发送requests的请求
        :param url: 目标url
        :param headers: 请求头
        :param params: 请求参数
        :param method: 请求方法
        :param is_json: 是否返回json数据
        :param verify: ssl验证
        :param need_handle_resp: 是否需要处理数据
        :return: 返回响应参数
        '''
        try:
            data = {'url': url, 'verify': verify, 'timeout': (10, 10)}
            if params is not None:
                data['params' if method == 'get' else 'data'] = json.dumps(params) if need_json_params else params
            if need_proxies:
                data['proxies'] = proxies
            if headers is not None:
                data['headers'] = headers

            if method == 'get':
                resp = requests.get(**data)
            elif method == 'post':
                resp = requests.post(**data)

            if resp.status_code is not 200:
                print(f'请求 [{url}] 失败. 返回状态码 [{resp.status_code}]. 失败原因 [{resp.reason}]', 2, '发送网络请求错误')
                return None
            return resp.json() if need_json_resp else resp.content if need_content else resp.text
        except Exception as e:
            # traceback.print_exception()
            print(f'请求 [{url}] 失败. 失败原因 [{e}]', 2, '发送网络请求错误')
            return None


def md5(_str):
    """32bit md5 encode"""
    h = hashlib.md5()
    h.update(_str.encode('utf-8'))
    return h.hexdigest()


class CloudFlareAPI:
    def __init__(self, email=CF.email, token=CF.token):
        self.cf = CloudFlare.CloudFlare(email=email, token=token)

    def create_domain(self, domain_name):
        try:
            _ = self.cf.zones.post(data={'name': domain_name})
            resp = {
                'status': True,
                'domain_id': _['id'],
                'domain': _['name'],
                'nameserver': _['name_servers'],
                'current_nameserver': _['original_name_servers'],
                'domain_registrar': _['original_registrar']
            }
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def delete_domain(self, domain_name):
        try:
            resp = self.cf.zones.delete(domain_name)
            resp['status'] = True
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def add_dns_by_domain(self, domain_id, dns_name,  content, dns_type='CNAME', proxied=False):
        try:
            _ = self.cf.zones.dns_records.post(domain_id, data={'proxied': proxied, 'name': dns_name, 'type': dns_type, 'content': content})
            resp = {'status': True, 'dns_id': _['id']}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def delete_dns_by_domain(self, dns_name):
        resp = self.cf.zones.dns_records.delete(dns_name)
        return resp


class AWSAPI:
    def __init__(self, api_type, aws_access_key_id=AWS.aws_access_key_id, aws_secret_access_key=AWS.aws_secret_access_key, region_name=None):
        if region_name is not None:
            self.client = boto3.client(api_type, region_name=region_name, aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key)
        else:
            self.client = boto3.client(api_type, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    def create_acm(self, main_domain, other_domains=[]):
        try:
            _ = self.client.request_certificate(DomainName=main_domain, ValidationMethod='DNS', SubjectAlternativeNames=other_domains)
            resp = {'status': True, 'id': _['CertificateArn']}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def get_acm_status(self, acmarn):
        try:
            _ = self.client.describe_certificate(CertificateArn=acmarn)
            domain_list = [{
                'domain': i['DomainName'],
                'dns_name': i['ResourceRecord']['Name'],
                'type': i['ResourceRecord']['Type'],
                'dns_value': i['ResourceRecord']['Value']
            } for i in _['Certificate']['DomainValidationOptions']]
            resp = {'status': True, 'domain_list': domain_list, 'domain_status': _['Certificate']['Status'], 'arn': _['Certificate']['CertificateArn']}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def delete_acm(self, acmarn):
        try:
            _ = self.client.delete_certificate(CertificateArn=acmarn)
            resp = {'status': True, 'msg': 'SUCCESS'}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def create_domain(self, acmarn, aliases=[]):
        distribution = AWS.create_domain_param
        distribution['CallerReference'] = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        distribution['ViewerCertificate']['ACMCertificateArn'] = acmarn
        distribution['ViewerCertificate']['Certificate'] = acmarn
        distribution['Aliases']['Items'] = aliases
        distribution['Aliases']['Quantity'] = len(aliases)
        try:
            _ = self.client.create_distribution(DistributionConfig=distribution)
            print(_)
            resp = {'status': True, 'etag': _['ETag'], 'arn': _['Distribution']['ARN'], 'distribution_id': _['Distribution']['Id'], 'domain': _['Distribution']['DomainName']}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp

    def get_domain(self, domainid):
        resp = self.client.get_distribution(Id=domainid)
        return resp

    def disabled_domain(self, domainid, headers_etag):
        distribution = AWS.create_domain_param
        distribution['Enabled'] = False
        distribution['ViewerCertificate'] = {
            'CloudFrontDefaultCertificate': True, 'MinimumProtocolVersion': 'TLSv1', 'CertificateSource': 'cloudfront'
        }
        resp = self.client.update_distribution(DistributionConfig=distribution, Id=domainid, IfMatch=headers_etag)
        return resp

    def delete_domain(self, domainid, headers_etag):
        try:
            _ = self.client.delete_distribution(Id=domainid, IfMatch=headers_etag)
            resp = {'status': True, 'msg': 'SUCCESS'}
        except Exception as e:
            resp = {'status': False, 'msg': e}
        return resp


if __name__ == '__main__':
    # 创建cloudflare域名
    cf1 = CloudFlareAPI()
    # resp = cf1.create_domain('kfr12.com')
    # print(resp)
    # 创建ACM证书
    acm = AWSAPI('acm', region_name=AWS.acm_region)
    # resp = acm.create_acm('kfr12.com', ['*.kfr12.com'])
    # print(resp)
    # 查看需要添加的CNAME记录值
    # resp = acm.get_acm_status('arn:aws:acm:us-east-1:644931538081:certificate/a9f8e341-70c6-4063-95e3-6f79c75eb8b9')
    # print(resp)
    # 添加acm的CNAME解析
    # resp = cf1.add_dns_by_domain('1ad350053b342409ec4311c37db78946', '_59bd8aba336d66226fe7502a587e0134.kfr12.com.', '_14dcaa4fd3ae38bb9d58a22e2426bf60.wggjkglgrm.acm-validations.aws.')
    # print(resp)
    # 创建cloudfront域名
    cf2 = AWSAPI('cloudfront')
    # {'status': True, 'etag': 'E12UDYMFRBE61X', 'arn': 'arn:aws:cloudfront::644931538081:distribution/EB70U6NAB470G',
    #  'distribution_id': 'EB70U6NAB470G', 'domain': 'dcyx7q0bverja.cloudfront.net'}
    # resp = cf2.create_domain('arn:aws:acm:us-east-1:644931538081:certificate/a9f8e341-70c6-4063-95e3-6f79c75eb8b9', ['kfr12.com', '*.kfr12.com'])
    # print(resp)
    # cf1.add_dns_by_domain('1ad350053b342409ec4311c37db78946', '@', 'dcyx7q0bverja.cloudfront.net')
    # resp = cf1.add_dns_by_domain('1ad350053b342409ec4311c37db78946', 'www', 'dcyx7q0bverja.cloudfront.net')
    # print(resp)
