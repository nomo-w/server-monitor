# coding: utf-8
# 未处理警报数据库

from db.base import DBbase
from config import Page

"""
CREATE TABLE `jk_unhandled_alert` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` int(11) NOT NULL,
  `status` varchar(200) DEFAULT '未处理',
  `description` varchar(200) DEFAULT NULL,
  `problem_type` varchar(200) NOT NULL,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class UnhandledAlert(DBbase):
    """未处理警报表"""
    def __init__(self):
        super().__init__()

    @staticmethod
    def _handle_query(start, end, machine_id, alert_type, is_active=1, need_end=True):
        where_sql = f'where is_active={is_active}'
        if machine_id:
            where_sql += f' and machine_id={machine_id}'
        if alert_type:
            where_sql += f' and problem_type="{alert_type}"'
        if start and end:
            where_sql += f' and create_time>="{start} 00:00:00" and create_time <="{end} 23:59:59"'
        return where_sql + ';' if need_end else where_sql

    def get_page(self, start, end, machine_id, alert_type, limit=Page.unhandled_limit):
        where_sql = self._handle_query(start, end, machine_id, alert_type)
        db_count = self.execute(f'select count(id) from jk_unhandled_alert {where_sql};', fetch=True)
        page_list = [i + 1 for i in range(db_count[0][0] // limit)]
        page_list = page_list if page_list else [1]
        if db_count[0][0] > limit and (db_count[0][0] % limit != 0):
            page_list.append(page_list[-1] + 1)
        return page_list, db_count[0][0]

    def get_alert(self, page, start, end, machine_id, alert_type, limit=Page.unhandled_limit):
        where_sql = self._handle_query(start, end, machine_id, alert_type, need_end=False)
        sql = f'select id,(select name from jk_machines where id=machine_id) as machine_name,' \
              f'(select ip from jk_machines where id=machine_id) as machine_ip,status,description,' \
              f'problem_type,create_time from jk_unhandled_alert {where_sql} limit {page*limit},{limit};'
        r = self.execute(sql, fetch=True)
        return [{
            'id': i[0],
            'machine': f'{f"{i[1]}({i[2]})" if i[1] else i[2]}',
            # 'machine_name': i[1],
            # 'machine_ip': i[2],
            'status': i[3],
            'description': i[4],
            'problem_type': i[5],
            'start_time': i[6].strftime('%Y-%m-%d %H:%M:%S')
        } for i in r] if r else []

    def update_alert(self, alert_id, status):
        r = self.execute(f'select machine_id,description,problem_type,create_time from jk_unhandled_alert where id={alert_id};', fetch=True)
        if r:
            sql = f'insert into jk_handled_alert (machine_id,status,description,problem_type,start_time) ' \
                  f'values ({r[0][0]},"{status}","{r[0][1]}","{r[0][2]}","{r[0][3]}");'
            count_type = "ignore_count" if status == "已忽略" else "handled_alert_count"
            self.execute(f'update jk_machines set {count_type}={count_type}+1,unhandled_alert_count=unhandled_alert_count-1 where id={r[0][0]};')
            self.execute(f'delete from jk_unhandled_alert where id={alert_id};')
            return '更新成功!' if self.execute(sql, commit=True) else '更新失败!'
        return '未找到!'

    def is_have_alert(self, machine_id, alert_type):
        sql = f'select id from jk_unhandled_alert where machine_id={machine_id} and problem_type="{alert_type}";'
        r = self.execute(sql, fetch=True)
        return r[0][0] if r else -1

    def create_alert(self, alert_type, description, machine_id):
        if self.is_have_alert(machine_id, alert_type) != -1:
            return False
        sql = f'insert into jk_unhandled_alert (machine_id,description,problem_type) values ({machine_id},"{description}","{alert_type}");'
        self.execute(f'update jk_machines set unhandled_alert_count=unhandled_alert_count+1 where id={machine_id};')
        return self.execute(sql, commit=True)
