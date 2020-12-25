# coding: utf-8
# NET数据库

from db.base import DBbase

"""
CREATE TABLE `jk_net` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` int(11) NOT NULL,
  `device` varchar(200) NOT NULL,
  `input` decimal(15,2) DEFAULT 0.00,
  `output` decimal(15,2) DEFAULT 0.00,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class NetDB(DBbase):
    """CPU表"""
    def __init__(self):
        super().__init__()

    def get_all_by_time_and_id(self, device, machine_id, _time=1):
        sql = f'select input,output,create_time from jk_net where machine_id={machine_id} and device="{device}" ' \
              f'and create_time>DATE_SUB(NOW(),INTERVAL {_time} HOUR);'
        r = self.execute(sql, fetch=True)
        return [{'input': round(float(i[0]), 2), 'output': round(float(i[1]), 2), 'time': i[2].strftime('%H:%M')} for i in r] if r else []
