from config import RedisSql, Remote, Alert, LogDefine
from db.unhandled_alert import UnhandledAlert
from db.myredis import mpop, mlen, mpush
from datetime import timedelta, date
from multiprocessing import Process
from db.processdb import ProcessDB
from db.interval import IntervalDB
from util.api import my_requests
from db.machines import Machine
from threading import Thread
from util import log
import traceback
import paramiko
import json
import time
import os


class SSHConnection:
    def __init__(self, host, username, pwd, port=22):
        self.host = host
        self.port = port
        self.username = username
        self.pwd = pwd
        self.__k = None

    def connect(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.pwd)
        self.__transport = transport

    def close(self):
        self.__transport.close()

    def upload(self, local_path, remote_path):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.put(local_path, remote_path)

    def cmd(self, command):
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport
        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(command)
        # 获取命令结果
        result = stdout.read()
        return result


def connection_machine():
    # 连接服务器
    while True:
        try:
            if mlen(RedisSql.cm_queue_name) > 0:
                machine_id = mpop(RedisSql.cm_queue_name)
                with Machine() as db:
                    data = db.get_machine_by_id(machine_id)
                    for i in range(3):
                        try:
                            ssh = SSHConnection(data['ip'], data['usr'], data['pwd'], data['ssh_port'])
                            ssh.connect()
                            result1 = ssh.cmd(Remote.remote_configuration_comm)
                            print(f'远程服务器[{data["ip"]}执行初始化命令成功, 执行结果[{result1}]', 0, '启动远程服务')
                            ssh.upload(Remote.local_py_path, Remote.remote_py_path)
                            ssh.upload(Remote.local_service_path, Remote.remote_service_path)
                            print(f'拷贝文件到远程服务器[{data["ip"]}]成功', 0, '启动远程服务')
                            result2 = ssh.cmd(Remote.remote_change_port_comm.format(port=data['http_port']))
                            result3 = ssh.cmd(Remote.remote_reload_comm)
                            result4 = ssh.cmd(Remote.remote_start_comm)
                            result5 = ssh.cmd(Remote.remote_enable_comm)
                            print(f'远程服务器[{data["ip"]}执行启动命令成功, 执行结果[{result5}]', 0, '启动远程服务')
                            ssh.close()
                            db.change_status_by_id(machine_id, '连接正常', 1)
                            with UnhandledAlert() as db1:
                                alert_id = db1.is_have_alert(machine_id, Alert.alert_type[0])
                                if alert_id != -1:
                                    db.update_alert(alert_id, '已处理')
                            break
                        except Exception as e:
                            if i == 2:
                                mpush(machine_id, RedisSql.cm_queue_name)
                                db.change_status_by_id(machine_id, '连接失败', 0)
                                with UnhandledAlert() as db1:
                                    db1.create_alert(Alert.alert_type[0], '连接失败, 请检查远程主机的网络连通性!', machine_id)
                            print(f'第{i+1}次连接远程服务器错误, 错误原因[{e}]', 2, '连接主机错误')
                            time.sleep(60)
                    time.sleep(60*5)
            else:
                time.sleep(60*10)
        except Exception as e:
            # traceback.print_exc()
            print(f'连接服务器进程错误, 错误原因[{e}]', 2, '连接主机错误')


def send_and_recv(ip, http_port, _type):
    try:
        data = my_requests(Remote.remote_http.format(ip=ip, port=http_port), 'post', params={'type': _type}, need_json_params=True)
        if data is not None and data['status']:
            mpush(json.dumps({'data': data["data"], 'http_port': http_port, 'ip': ip, 'type': _type, 'status': True, 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}), RedisSql.machine_info_queue_name)
        else:
            mpush(json.dumps({
                'ip': ip,
                'type': _type,
                'http_port': http_port,
                'status': False,
                'data': f'获取远程主机数据失败',
                'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }), RedisSql.machine_info_queue_name)
            print(f'获取[{ip}:{_type}]信息失败', 2, f'{_type}错误')
    except Exception as e:
        mpush(json.dumps({
            'ip': ip,
            'type': _type,
            'http_port': http_port,
            'status': False,
            'data': f'获取远程主机[{ip}]的{_type}信息失败[{e}]',
            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }), RedisSql.machine_info_queue_name)
        print(f'获取[{ip}:{_type}]信息失败, 失败原因[{e}]', 2, f'{_type}错误')


def get_machine(_type):
    print(f'检测[{_type}]程序启动', 0, f'{_type}')
    while True:
        try:
            with IntervalDB() as db:
                interval = db.get_interval_by_type(_type)
            with Machine() as db:
                machine_list = db.get_machines(simple=True, only_ip=True)
            for i in machine_list:
                Thread(target=send_and_recv, args=(i['machine'], i['http_port'], _type)).start()
            time.sleep(60*interval)
        except Exception as e:
            # traceback.print_exc()
            print(f'检测[{_type}]程序出错, 失败原因[{e}]', 2, f'{_type}错误')
            time.sleep(60)


def handle_machine_info():
    while True:
        try:
            num = mlen(RedisSql.machine_info_queue_name)
            if num > 0:
                with Machine() as db:
                    for n in range(num):
                        data = json.loads(mpop(RedisSql.machine_info_queue_name))
                        machine_info = db.get_alarm_by_ip(data['ip'])
                        print(f'处理远程主机[{data["ip"]}:{data["type"]}:{data["status"]}]数据', 0, '处理主机信息')
                        with UnhandledAlert() as db1:
                            if data['status']:
                                db.create_jk_by_machine_id(data['type'], data['data'], machine_info['id'], data['time'])
                                alert_id = db1.is_have_alert(machine_info['id'], Alert.alert_type[1])
                                if alert_id != -1:
                                    db.change_status_by_id(machine_info['id'], '连接正常', 1)
                                    db1.update_alert(alert_id, '已处理')
                                if data['type'] == 'mem':
                                    with ProcessDB() as db2:
                                        db2.create_process(data['data']['process'], machine_info['id'], 'mem')
                                    if data['data']['mem_percent'] > machine_info['mem_alarm']:
                                        print(f'远程主机[{data["ip"]}]内存使用量过高,当前已使用{data["data"]["mem_used"]}G!', 1, '主机警报信息')
                                        db1.create_alert(Alert.alert_type[2], f'内存使用量过高,当前已使用{data["data"]["mem_used"]}G!', machine_info['id'])
                                    else:
                                        alert_id = db1.is_have_alert(machine_info['id'], Alert.alert_type[2])
                                        if alert_id != -1:
                                            print(f'远程主机[{data["ip"]}]的内存警报已解除', 0, '主机警报信息')
                                            db1.update_alert(alert_id, '已处理')
                                elif data['type'] == 'cpu':
                                    with ProcessDB() as db2:
                                        db2.create_process(data['data']['process'], machine_info['id'], 'cpu')
                                    if data['data']['cpu_percent'] > machine_info['cpu_alarm']:
                                        print(f'远程主机[{data["ip"]}]cpu使用量过高,当前已使用{data["data"]["cpu_percent"]}%!', 1, '主机警报信息')
                                        db1.create_alert(Alert.alert_type[3], f'cpu使用量过高,当前已使用{data["data"]["cpu_percent"]}%!', machine_info['id'])
                                    else:
                                        alert_id = db1.is_have_alert(machine_info['id'], Alert.alert_type[3])
                                        if alert_id != -1:
                                            print(f'远程主机[{data["ip"]}]的cpu警报已解除', 0, '主机警报信息')
                                            db1.update_alert(alert_id, '已处理')
                            else:
                                db1.create_alert(Alert.alert_type[1], f'与远程主机{data["ip"]}连接失败,请检查远程主机{data["http_port"]}端口是否开放!', machine_info['id'])
                                db.change_status_by_id(machine_info['id'], '断开连接', 1)
                time.sleep(60)
            else:
                time.sleep(60)
        except Exception as e:
            # traceback.print_exc()
            print(f'处理远程主机信息失败, 失败原因[{e}]', 2, '处理主机信息错误')


def timer_zsq(func):
    def inner(*args, **kwargs):
        day = time.strftime("%Y-%m-%d", time.localtime())
        while True:
            today = time.strftime("%Y-%m-%d", time.localtime())
            if day != today:
                func(*args, **kwargs)
                day = today
            time.sleep(60 * 60)
    return inner


@timer_zsq
def del_old_log_file():
    today = time.strftime("%Y-%m-%d", time.localtime())
    yesterday = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
    lp = LogDefine.logpath
    for f in os.listdir(lp):
        if today not in f and yesterday not in f:
            print(f'删除日志文件 [{lp}/{f}]', 0, '删除日志')
            os.remove(f'{lp}/{f}')


@timer_zsq
def del_last24hours_jk():
    with Machine() as db:
        print(f'删除24小时之前的监控数据', 0, '删除数据')
        db.del_old_jk(24)


if __name__ == '__main__':
    log.init()
    # 删除旧日志
    Process(target=del_old_log_file, name='del_old_log_server').start()
    # 删除过去24小时的监控数据
    Process(target=del_last24hours_jk, name='del_last24hours_jk_server').start()
    # 连接服务器
    Process(target=connection_machine, name='connection_machine_server').start()
    with IntervalDB() as db:
        interval_list = db.get_interval()
    for i in interval_list:
        # 获取服务器信息
        Process(target=get_machine, args=(i,), name=f'get_{i}_server').start()
        time.sleep(5)
    # 处理服务器信息
    handle_machine_info()
