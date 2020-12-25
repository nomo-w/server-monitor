# coding: utf-8
import os


class CF:
    email = 'xxxxxxx@xxxxxxx.net'
    token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'


class AWS:
    acm_success_status = 'ISSUED'
    acm_region = 'us-east-1'
    aws_access_key_id = 'XXXXXXXXXXXXX'
    aws_secret_access_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    create_domain_param = {
                'CallerReference': 'xxxx',
                'Aliases': {'Quantity': 0,  'Items': []},
                'DefaultRootObject': '',
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': 'ELB-demo1-797484051',
                        'DomainName': 'demo1-797484051.ap-northeast-1.elb.amazonaws.com',
                        'OriginPath': '',
                        'CustomHeaders': {'Quantity': 0},
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'http-only',
                            'OriginSslProtocols': {'Quantity': 3, 'Items': ['TLSv1', 'TLSv1.1', 'TLSv1.2']},
                            'OriginReadTimeout': 30,
                            'OriginKeepaliveTimeout': 5
                        },
                        'ConnectionAttempts': 3,
                        'ConnectionTimeout': 10,
                        'OriginShield': {'Enabled': False}
                    }]
                },
                'OriginGroups': {'Quantity': 0},
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'ELB-demo1-797484051',
                    'TrustedSigners': {'Enabled': False, 'Quantity': 0},
                    'TrustedKeyGroups': {'Enabled': False, 'Quantity': 0},
                    'ViewerProtocolPolicy': 'allow-all',
                    'AllowedMethods': {
                        'Quantity': 7,
                        'Items': ['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'DELETE'],
                        'CachedMethods': {'Quantity': 2, 'Items': ['GET', 'HEAD']}
                    },
                    'SmoothStreaming': False,
                    'Compress': True,
                    'LambdaFunctionAssociations': {'Quantity': 0},
                    'FieldLevelEncryptionId': '',
                    'ForwardedValues': {
                        'QueryString': True,
                        'Cookies': {'Forward': 'all'},
                        'Headers': {
                            'Quantity': 10,
                            'Items': [
                                'Accept-Charset',
                                'Authorization',
                                'Origin',
                                'Accept',
                                'Referer',
                                'Host',
                                'Accept-Encoding',
                                'Accept-Language',
                                'Accept-Datetime',
                                'CloudFront-Is-Desktop-Viewer'
                            ]
                        },
                        'QueryStringCacheKeys': {'Quantity': 0}
                    },
                    'MinTTL': 0,
                    'DefaultTTL': 86400,
                    'MaxTTL': 31536000
                },
                'CacheBehaviors': {'Quantity': 0},
                'CustomErrorResponses': {'Quantity': 0},
                'Comment': '',
                'Logging': {
                    'Enabled': False,
                    'IncludeCookies': False,
                    'Bucket': '',
                    'Prefix': ''
                },
                'PriceClass': 'PriceClass_200',
                'Enabled': True,
                'ViewerCertificate': {
                    # 'ACMCertificateArn': '',
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.2_2018',
                    # 'Certificate': '',
                    'CertificateSource': 'acm'
                },
                'Restrictions': {'GeoRestriction': {'RestrictionType': 'none', 'Quantity': 0}},
                'WebACLId': '',
                'HttpVersion': 'http2',
                'IsIPV6Enabled': True
            }


class Page:
    """分页配置"""
    # 每页数量
    unhandled_limit = 10
    home_page_machine_limit = 10
    handled_limit = 20
    machines_limit = 20
    user_limit = 20


class LogDefine:
    """log定义"""
    logpath = os.path.abspath(os.path.dirname(__file__)) + '/logs'
    request_log_file = logpath + '/{}_request.log'
    log_level = {
        0: 'DEBUG',
        1: 'WARING',
        2: 'ERROR'
    }


class Return_Statua_Code:
    """返回状态定义"""
    ok = 200
    error = 500


class Sql:
    """mysql连接配置"""
    host = '127.0.0.1'
    password = 'xxxxxxxx'
    port = 3306
    user = 'root'
    db = 'cmdb'
    max_cached = 20
    kl_message_id = -10
    min_cache_limit = 20000
    max_cache_limit = 50000


class RedisSql:
    host = '127.0.0.1'
    port = 6379
    db = 0
    cm_queue_name = "create_machine_list"
    machine_info_queue_name = "machine_info"
    # job_status_code = {'pending': '300', 'success': '200', 'failed': '500'}


class Remote:
    local_py_path = os.path.abspath(os.path.dirname(__file__)) + '/agent_web.py'
    local_service_path = os.path.abspath(os.path.dirname(__file__)) + '/agent_web.service'
    remote_py_path = '/root/agent_web.py'
    remote_service_path = '/etc/systemd/system/agent_web.service'
    remote_http = 'http://{ip}:{port}/api/get_info'
    remote_configuration_comm = 'yum install -y python36 python36-devel python36-setuptools gcc && easy_install-3.6 pip && pip3 install flask flask-cors psutil gunicorn'
    remote_change_port_comm = "sed -i 's/8808/{port}/' " + remote_service_path
    remote_reload_comm = 'systemctl daemon-reload'
    remote_start_comm = 'systemctl start agent_web'
    remote_enable_comm = 'systemctl enable agent_web'


class Alert:
    alert_type = {0: 'ping', 1: 'http', 2: 'memory', 3: 'cpu', 4: 'network'}
