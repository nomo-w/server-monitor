# coding: utf-8
# MEM数据库

from db.base import DBbase

"""
CREATE TABLE `jk_mem` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` int(11) NOT NULL,
  `used` decimal(15,2) DEFAULT 0.00,
  `percent` decimal(15,2) DEFAULT 0.00,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class MemDB(DBbase):
    """CPU表"""
    def __init__(self):
        super().__init__()

    def get_all_by_time(self, machine_id, _time=1):
        sql = f'select used,create_time from jk_mem where machine_id={machine_id} and create_time>DATE_SUB(NOW(),INTERVAL {_time} HOUR);'
        r = self.execute(sql, fetch=True)
        return [{'used': round(float(i[0]), 2), 'time': i[1].strftime('%H:%M')} for i in r] if r else []
