# coding: utf-8
# 服务器数据库

import time
from config import Page
from db.base import DBbase
from db.users import UserDB

"""
CREATE TABLE `jk_machines` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) DEFAULT NULL,
  `ip` varchar(200) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  `status` varchar(200) DEFAULT '连接中',
  `need_get_info` tinyint(1) DEFAULT 0,
  `unhandled_alert_count` varchar(200) DEFAULT 0,
  `handled_alert_count` varchar(200) DEFAULT 0,
  `ignore_count` varchar(200) DEFAULT 0,
  `mem_alarm_value` decimal(15,2) DEFAULT 80.00,
  `cpu_alarm_value` decimal(15,2) DEFAULT 80.00,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `username` varchar(200) NOT NULL,
  `password` varchar(200) NOT NULL,
  `ssh_port` int(11) DEFAULT 22,
  `http_port` int(11) DEFAULT 8808,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY (`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class Machine(DBbase):
    """已处理警报表"""
    def __init__(self):
        super().__init__()

    def get_machine_by_id(self, machine_id):
        r = self.execute(f'select ip,username,password,ssh_port,http_port from jk_machines where id={machine_id};', fetch=True)
        return {'ip': r[0][0], 'usr': r[0][1], 'pwd': r[0][2], 'ssh_port': r[0][3], 'http_port': r[0][4]}

    @staticmethod
    def _handle_query(start, end, machine, need_end=True):
        where_sql = ''
        if start and end:
            where_sql += f'{" and" if where_sql else "where"} time>="{start} 00:00:00" and time <="{end} 23:59:59"'
        if machine:
            where_sql += f'{" and" if where_sql else "where"} name like "%{machine}%" or ip like "%{machine}%"'
        return where_sql + ';' if need_end else where_sql

    def get_page(self, start, end, machine, limit):
        where_sql = self._handle_query(start, end, machine)
        db_count = self.execute(f'select count(id) from jk_machines {where_sql}', fetch=True)
        page_list = [i + 1 for i in range(db_count[0][0] // limit)]
        page_list = page_list if page_list else [1]
        if db_count[0][0] > limit and (db_count[0][0] % limit != 0):
            page_list.append(page_list[-1] + 1)
        return page_list, db_count[0][0]

    def get_machines_home_page(self, page, machine, start, end, limit=Page.home_page_machine_limit):
        where_sql = self._handle_query(start, end, machine, need_end=False)

        sql = f'select name,ip,unhandled_alert_count,handled_alert_count,ignore_count,status from jk_machines {where_sql} limit {page*limit},{limit};'
        r = self.execute(sql, fetch=True)
        return [{
            'machine': f'{f"{i[0]}({i[1]})" if i[0] else i[1]}',
            # 'name': i[0],
            # 'ip': i[1],
            'unhandled_alert_count': i[2],
            'handled_alert_count': i[3],
            'ignore_count': i[4],
            'status': i[5]
        } for i in r] if r else []

    def get_machines(self, page=0, machine=None, start=None, end=None, limit=Page.machines_limit, simple=False, only_ip=False):
        if simple:
            if only_ip:
                r = self.execute(f'select id,name,ip,http_port from jk_machines where is_active=1 and need_get_info=1;', fetch=True)
            else:
                r = self.execute(f'select id,name,ip,http_port from jk_machines where is_active=1;', fetch=True)
        else:
            where_sql = self._handle_query(start, end, machine, need_end=False)
            r = self.execute(f'select id,name,ip,description,status,unhandled_alert_count,handled_alert_count,'
                             f'ignore_count,mem_alarm_value,cpu_alarm_value,create_time,http_port,is_active '
                             f'from jk_machines {where_sql} limit {page * limit},{limit};', fetch=True)
        return [{'id': i[0], 'http_port': i[3], 'machine': i[2] if only_ip else f'{f"{i[1]}({i[2]})" if i[1] else i[2]}'} if simple else {
            'id': i[0],
            'name': i[1],
            'ip': i[2],
            'description': i[3],
            'status': i[4],
            'unhandled_alert_count': i[5],
            'handled_alert_count': i[6],
            'ignore_count': i[7],
            'mem_alarm_value': round(float(i[8]), 2),
            'cpu_alarm_value': round(float(i[9]), 2),
            'create_time': i[10].strftime('%Y-%m-%d %H:%M:%S'),
            'http_port': i[11],
            'is_active': i[12]
        } for i in r] if r else []

    def change_machine_by_id(self, login_user_id, machine_id, name, description, mem_alarm, cpu_alarm, http_port, is_active):
        with UserDB() as db:
            if db.get_auth(login_user_id) == 'admin':
                sql = f'update jk_machines set name="{name}",description="{description}",mem_alarm_value={mem_alarm}' \
                      f',cpu_alarm_value={cpu_alarm},is_active={is_active},need_get_info={is_active},http_port={http_port}' \
                      f''',status="{"已禁用" if is_active == 0 else "连接正常"}" where id={machine_id};'''
                return '修改成功!' if self.execute(sql, commit=True) else '修改失败!'
            return '您无此权限, 请联系管理员!'

    def is_have_machine(self, ip):
        return self.execute(f'select id from jk_machines where ip="{ip}";')

    def create_machine(self, login_user_id, name, ip, description, mem_alarm, cpu_alarm, usr, pwd, ssh_port, http_port, need_auto_connection):
        with UserDB() as db:
            if db.get_auth(login_user_id) == 'admin':
                if self.is_have_machine(ip):
                    return '该主机已存在, 请更换ip重试!', 0
                sql = f'insert into jk_machines (name,ip,description,mem_alarm_value,cpu_alarm_value,username,password' \
                      f',ssh_port,http_port,need_get_info) values ("{name}","{ip}","{description}",{mem_alarm},' \
                      f'{cpu_alarm},"{usr}","{pwd}",{ssh_port},{http_port},{0 if need_auto_connection == "1" else 1});'
                r = '创建成功!' if self.execute(sql, commit=True) else '创建失败!'
                if r == '创建成功!':
                    machine_id = self.execute('SELECT LAST_INSERT_ID();', fetch=True)[0][0]
                else:
                    machine_id = 0
                return r, machine_id
            return '您无此权限, 请联系管理员!', 0

    def change_status(self, login_user_id, machine_id, is_active):
        # 更改服务器的is_active状态
        with UserDB() as db:
            if db.get_auth(login_user_id) == 'admin':
                if is_active == '0':
                    # 禁用
                    sql = f'update jk_machines set is_active={is_active},status="已禁用",need_get_info={is_active} where id={machine_id};'
                else:
                    # 启用
                    if self.execute(f'select id from jk_machines where is_active=1 and id={machine_id};'):
                        return '修改失败!'
                    else:
                        sql = f'update jk_machines set is_active={is_active},status="连接正常",need_get_info={is_active} where id={machine_id};'
                r = self.execute(sql, commit=True)
                return '修改成功!' if r else '修改失败!'
            return '您无此权限, 请联系管理员!'

    def change_status_by_id(self, machine_id, status, need_get_info):
        # 更改服务器的状态
        return self.execute(f'update jk_machines set status="{status}",need_get_info={need_get_info} where id={machine_id};', commit=True)

    def get_alarm_by_ip(self, ip):
        r = self.execute(f'select id,name,mem_alarm_value,cpu_alarm_value from jk_machines where ip="{ip}";', fetch=True)
        return {'id': r[0][0], 'name': r[0][1], 'mem_alarm': round(float(r[0][2]), 2), 'cpu_alarm': round(float(r[0][3]), 2)} if r else {}

    def create_jk_by_machine_id(self, _type, data, machine_id, _time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), commit=True):
        if _type == 'cpu':
            self.execute(f'insert into jk_cpu (machine_id,utilization,create_time) values ({machine_id},'
                         f'{data["cpu_percent"]},"{_time}");')
        elif _type == 'mem':
            self.execute(f'insert into jk_mem (machine_id,used,percent,create_time) values ({machine_id},'
                         f'{data["mem_used"]},{data["mem_percent"]},"{_time}");')
        elif _type == 'net':
            for i in data["net_info"]:
                self.execute(f'insert into jk_net (machine_id,device,input,output,create_time) values ({machine_id},'
                             f'"{i["device"]}",{i["input"]},{i["output"]},"{_time}")')
        if commit:
            self.commit()

    def get_net_by_id(self, machine_id):
        r = self.execute(f'select distinct device from jk_net where is_active=1 and machine_id={machine_id};', fetch=True)
        return [i[0] for i in r] if r else ['eth0']

    def del_old_jk(self, _time=24):
        self.execute(f'delete from jk_cpu where create_time<DATE_SUB(NOW(),INTERVAL {_time} HOUR);')
        self.execute(f'delete from jk_mem where create_time<DATE_SUB(NOW(),INTERVAL {_time} HOUR);')
        self.execute(f'delete from jk_net where create_time<DATE_SUB(NOW(),INTERVAL {_time} HOUR);', commit=True)
