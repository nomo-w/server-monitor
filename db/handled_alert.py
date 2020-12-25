# coding: utf-8
# 已处理警报数据库

from db.base import DBbase
from config import Page

"""
CREATE TABLE `jk_handled_alert` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` int(11) NOT NULL,
  `status` varchar(200) DEFAULT '已处理',
  `description` varchar(200) DEFAULT NULL,
  `problem_type` varchar(200) NOT NULL,
  `start_time` timestamp NULL,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class HandledAlert(DBbase):
    """已处理警报表"""
    def __init__(self):
        super().__init__()

    @staticmethod
    def _handle_query(start, end, machine_id, alert_type, is_active=1, need_end=True):
        where_sql = f'where is_active={is_active}'
        if machine_id:
            where_sql += f' and machine_id={machine_id}'
        if alert_type:
            where_sql += f' and alert_type={alert_type}'
        if start and end:
            where_sql += f' and time>="{start} 00:00:00" and time <="{end} 23:59:59"'
        return where_sql + ';' if need_end else where_sql

    def get_page(self, start, end, machine_id, alert_type, limit=Page.handled_limit):
        where_sql = self._handle_query(start, end, machine_id, alert_type)
        db_count = self.execute(f'select count(id) from jk_handled_alert {where_sql}', fetch=True)
        page_list = [i + 1 for i in range(db_count[0][0] // limit)]
        page_list = page_list if page_list else [1]
        if db_count[0][0] > limit and (db_count[0][0] % limit != 0):
            page_list.append(page_list[-1] + 1)
        return page_list, db_count[0][0]

    def get_alert(self, page, start, end, machine_id, alert_type, limit=Page.handled_limit):
        where_sql = self._handle_query(start, end, machine_id, alert_type, need_end=False)
        sql = f'select id,(select name from jk_machines where id=machine_id) as machine_name,' \
              f'(select ip from jk_machines where id=machine_id) as machine_ip,status,description,' \
              f'problem_type,start_time,create_time from jk_handled_alert {where_sql} limit {page*limit},{limit};'
        r = self.execute(sql, fetch=True)
        return [{
            'id': i[0],
            'machine': f'{f"{i[1]}({i[2]})" if i[1] else i[2]}',
            # 'machine_name': i[1],
            # 'machine_ip': i[2],
            'status': i[3],
            'description': i[4],
            'problem_type': i[5],
            'start_time': i[6].strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': i[7].strftime('%Y-%m-%d %H:%M:%S')
        } for i in r] if r else []
