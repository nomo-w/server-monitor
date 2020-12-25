# coding: utf-8


from db.unhandled_alert import UnhandledAlert
from db.handled_alert import HandledAlert
from db.myredis import mpush, mdelete
from db.interval import IntervalDB
from db.processdb import ProcessDB
from flask import Flask, request
from db.machines import Machine
from flask_cors import CORS
from db.users import UserDB
from db.cpudb import CpuDB
from db.memdb import MemDB
from db.netdb import NetDB
from util import api, log
from config import *


app = Flask('web')
CORS(app, supports_credentials=True)
app.secret_key = 'ABCAz47j22AA#R~X@H!jLwf/A'
log.init()


# --------------------------------------------------------
# 首页
# 未处理警报/已处理警报/系统状态
# --------------------------------------------------------
@app.route('/api/home/action', methods=['post'])
@api.is_login_zsq
@api.handle_api_zsq('/api/home/action', 'POST')
def home_action():
    action_type = request.form['action_type']
    page, start, end = request.form.get('page', 0), request.form.get('start', None), request.form.get('end', None)
    machine_id, alert_type = request.form.get('machine_id', None), request.form.get('alert_type', None)
    page = int(page) - 1 if page not in (None, 'none', '', 'None', 'null', 0, '0') else 0
    if action_type == 'unhandled_alert':
        # 未处理警报
        with UnhandledAlert() as db:
            page_list, total = db.get_page(start, end, machine_id, alert_type)
            ua = db.get_alert(page, start, end, machine_id, alert_type)
            data, code = {'value_list': ua, 'page_list': page_list, 'total': total}, 0
    elif action_type == 'handled_alert':
        # 已处理警报
        with HandledAlert() as db:
            page_list, total = db.get_page(start, end, machine_id, alert_type)
            ua = db.get_alert(page, start, end, machine_id, alert_type)
            data, code = {'value_list': ua, 'page_list': page_list, 'total': total}, 0
    elif action_type == 'system_status':
        # 系统状态
        machine = request.form.get('machine', None)
        with Machine() as db:
            page_list, total = db.get_page(start, end, machine, Page.handled_limit)
            ua = db.get_machines_home_page(page, machine, start, end)
            data, code = {'value_list': ua, 'page_list': page_list, 'total': total}, 0
    elif action_type == 'ignore_alert':
        alert_id = request.form['alert_id']
        with UnhandledAlert() as db:
            data = db.update_alert(alert_id, '已忽略')
            code = 0 if data == '更新成功!' else -1
    else:
        data, code = 'ERROR', -1
    return api.handle_httpresponse(data, code)


# --------------------------------------------------------
# 服务器列表页面
# 获取所有服务器/修改服务器/添加服务器/单独修改状态
# --------------------------------------------------------
@app.route('/api/machine/action', methods=['post'])
@api.is_login_zsq
@api.handle_api_zsq('/api/machine/action', 'POST')
def machine_action():
    action_type = request.form['action_type']
    with Machine() as db:
        if action_type == 'get_machines':
            start, end = request.form.get('start', None), request.form.get('end', None)
            page, machine = request.form.get('page', 0), request.form.get('machine', None)
            page = int(page) - 1 if page not in (None, 'none', '', 'None', 'null', 0, '0') else 0
            page_list, total = db.get_page(start, end, machine, Page.machines_limit)
            ua = db.get_machines(page, machine, start, end)
            data, code = {'value_list': ua, 'page_list': page_list, 'total': total}, 0
        elif action_type == 'get_simple_machines':
            with IntervalDB() as db1:
                data = db1.get_interval()
            data['machine_list'], code = db.get_machines(simple=True), 0
        elif action_type == 'get_alert_type':
            data, code = [Alert.alert_type[i] for i in Alert.alert_type], 0
        elif action_type == 'get_net':
            machine_id = request.form['machine_id']
            data, code = db.get_net_by_id(machine_id), 0
        elif action_type == 'change_machine':
            machine_id, http_port = request.form['machine_id'], request.form['http_port']
            mem_alarm, cpu_alarm = request.form['mem_alarm'], request.form['cpu_alarm']
            name, description, is_active = request.form['name'], request.form['description'], request.form['is_active']
            data = db.change_machine_by_id(api.get_uid(), machine_id, name, description, mem_alarm, cpu_alarm, http_port, is_active)
            code = 0 if data == '修改成功!' else -1
        elif action_type == 'add_machine':
            name, description = request.form.get('name', ''), request.form.get('description', '')
            mem_alarm, cpu_alarm = request.form['mem_alarm'], request.form['cpu_alarm']
            need_auto_connection, ip = request.form['need_auto_connection'], request.form['ip']
            http_port = request.form['http_port']
            if need_auto_connection == '1':
                # 需要自动发现服务器
                user, pwd, ssh_port = request.form['machine_user'], request.form['machine_pwd'], request.form['ssh_port']
            else:
                # 不需要自动发现
                user, pwd, ssh_port = '', '', 22
            data, machine_id = db.create_machine(api.get_uid(), name, ip, description, mem_alarm, cpu_alarm, user, pwd, ssh_port, http_port, need_auto_connection)
            if need_auto_connection == '1' and machine_id != 0:
                mpush(machine_id, RedisSql.cm_queue_name)
            code = 0 if data == '创建成功!' else -1
        elif action_type == 'change_status':
            machine_id, is_active = request.form['machine_id'], request.form['is_active']
            data = db.change_status(api.get_uid(), machine_id, is_active)
            code = 0 if data == '修改成功!' else -1
        elif action_type == 'change_interval':
            interval, interval_type = request.form['time'], request.form['type']
            with IntervalDB() as db1:
                data = db1.change_interval(interval_type, interval)
                code = 0 if data == '修改成功!' else -1
        else:
            data, code = 'ERROR', -1
    return api.handle_httpresponse(data, code)


# --------------------------------------------------------
# 获取机器各类信息
# CPU/内存/网络
# --------------------------------------------------------
@app.route('/api/info/action', methods=['post'])
@api.is_login_zsq
@api.handle_api_zsq('/api/info/action', 'POST')
def machine_info():
    info_type = request.form['action_type']
    machine_id = request.form['machine_id']
    _time = request.form.get('time', 1)
    if info_type == 'cpu':
        with ProcessDB() as db:
            process = db.get_process_by_id_and_type(machine_id, 'cpu')
        with CpuDB() as db:
            cpuinfo = db.get_all_by_time(machine_id, _time)
        data, code = {'process_list': process, 'info_list': cpuinfo}, 0
    elif info_type == 'mem':
        with ProcessDB() as db:
            process = db.get_process_by_id_and_type(machine_id, 'mem')
        with MemDB() as db:
            meminfo = db.get_all_by_time(machine_id, _time)
        data, code = {'process_list': process, 'info_list': meminfo}, 0
    elif info_type == 'net':
        device = request.form['device']
        with NetDB() as db:
            data, code = db.get_all_by_time_and_id(device, machine_id, _time), 0
    else:
        data, code = 'ERROR', -1
    return api.handle_httpresponse(data, code)


# --------------------------------------------------------
# 关于用户的操作
# 用户系统 - 登入/登出/修改密码/查看/删除/新建
# --------------------------------------------------------
@app.route('/api/user/login_failed')
@api.handle_api_zsq('/api/user/login_failed', 'GET')
def login_failed():
    """登陆失败后的返回"""
    return api.handle_httpresponse('未登录!')


@app.route('/api/user/login', methods=['post'])
@api.handle_api_zsq('/api/user/login', 'POST')
def login_request():
    user, password = request.form['user'], request.form['password']
    with UserDB() as db:
        user_id = db.is_right_password(user, password)
    if user_id != -1:
        # 找到用户
        token = api.create_token(user_id)
        # login.login(user_id)
        return api.handle_httpresponse({'msg': '登陆成功!', 'token': token}, 0)
    return api.handle_httpresponse('账户或密码错误!')


@app.route('/api/user/action', methods=['post'])
@api.is_login_zsq
@api.handle_api_zsq('/api/user/action', 'POST')
def user_action():
    action_type = request.form['action_type']
    with UserDB() as db:
        if action_type == 'logout':
            # 登出
            mdelete(request.headers['token'])
            data, code = '登出!', 0
        elif action_type == 'change_self_password':
            # 修改自己的密码
            newpassword = request.form['password']
            if db.change_password(api.get_uid(), newpassword):
                data, code = '修改成功!', 0
            else:
                data, code = '修改失败!', -1
        elif action_type == 'get_all':
            # 获取所有用户
            start, end = request.form.get('start', None), request.form.get('end', None)
            page, user = request.form.get('page', 0), request.form.get('user', None)
            page = int(page) - 1 if page not in (None, 'none', '', 'None', 'null', 0, '0') else 0
            page_list, total = db.get_page(start, end, user)
            ua = db.get_all(page, start, end, user)
            data, code = {'value_list': ua, 'page_list': page_list, 'total': total}, 0
        elif action_type == 'del_user':
            # 删除用户
            del_user_id = request.form['user_id']
            data = db.del_user(api.get_uid(), del_user_id)
            code = 0 if data == '成功删除!' else -1
        elif action_type == 'create_user':
            # 创建用户
            user, password, auth = request.form['user'], request.form['password'], request.form['auth']
            data = db.create_user(api.get_uid(), user, password, auth)
            code = 0 if data == '添加成功!' else -1
        else:
            data, code = 'ERROR', -1
    return api.handle_httpresponse(data, code)


# Main
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, threaded=True)