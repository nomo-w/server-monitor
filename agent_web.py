# coding: utf-8

from flask import Flask, request
from flask_cors import CORS
import psutil
import time
import json
import os

app = Flask('web')
CORS(app, supports_credentials=True)
app.secret_key = 'ABCAz47j22AA#R~X@H!jLwf/A'


class Agent:
    @staticmethod
    def get_mem_info():
        mem_info = psutil.virtual_memory()
        # 内存总量
        mem_total = int(mem_info.total/1024/1024/1024)
        # 内存使用总量(单位G)
        mem_used = round(float(mem_info.used/1024/1024/1024), 2)
        # 内存使用量百分比
        mem_percent = mem_info.percent
        return mem_total, mem_used, mem_percent

    @staticmethod
    def get_cpu_info():
        # CPU的使用率
        cpu_info = psutil.cpu_percent(1)
        psutil.cpu_count()
        return cpu_info

    @staticmethod
    def _getNetworkData():
        # 获取网卡流量信息
        recv = {}
        sent = {}
        data = psutil.net_io_counters(pernic=True)
        interfaces = data.keys()
        for interface in interfaces:
            recv.setdefault(interface, data.get(interface).bytes_recv)
            sent.setdefault(interface, data.get(interface).bytes_sent)
        return interfaces, recv, sent

    @classmethod
    def get_rate(cls):
        # 计算网卡流量速率
        interfaces, oldRecv, oldSent = cls._getNetworkData()
        time.sleep(1)
        interfaces, newRecv, newSent = cls._getNetworkData()
        networkIn = {}
        networkOut = {}
        for key in interfaces:
            networkIn.setdefault(key, float('%.2f' %((newRecv.get(key) - oldRecv.get(key)) / 1024)))
            networkOut.setdefault(key, float('%.2f' %((newSent.get(key) - oldSent.get(key)) / 1024)))
        return interfaces, networkIn, networkOut

    @staticmethod
    def get_top_process(process_type, top=5):
        if process_type == 'cpu':
            comm = f'ps -aux | sort -k3nr | head -{top}'
        elif process_type == 'mem':
            comm = f'ps -aux | sort -k4nr | head -{top}'
        result = os.popen(comm).read()
        data = []
        for i in result.split('\n'):
            if i:
                _ = [x for x in i.split(' ') if x]
                data.append({'user': _[0], 'pid': _[1], '%': f'{_[3]}%' if process_type == 'mem' else f'{_[2]}%', 'process': " ".join(_[10:])})
        return data


@app.route('/api/get_info', methods=['post'])
def index():
    try:
        data = json.loads(request.data.decode())
        _type = data['type']
        resp = {'status': True, 'type': _type, 'data': {}}
        if _type == 'mem':
            process = Agent.get_top_process('mem', data.get('top', 5))
            mem_total, mem_used, mem_percent = Agent.get_mem_info()
            resp['data']['mem_total'] = mem_total
            resp['data']['mem_used'] = mem_used
            resp['data']['mem_percent'] = mem_percent
            resp['data']['process'] = process
        elif _type == 'cpu':
            process = Agent.get_top_process('cpu', data.get('top', 5))
            cpu_percent = Agent.get_cpu_info()
            resp['data']['cpu_percent'] = cpu_percent
            resp['data']['process'] = process
        elif _type == 'net':
            key_info, net_in, net_out = Agent.get_rate()
            resp['data']['net_info'] = []
            for key in key_info:
                if 'lo' != key:
                    # lo 是linux的本机回环网卡
                    resp['data']['net_info'].append({'device': key, 'input': net_in.get(key), 'output': net_out.get(key)})
        else:
            resp['status'] = False
        return json.dumps(resp)
    except:
        return json.dumps({'status': False})


# Main
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8808, threaded=True)
