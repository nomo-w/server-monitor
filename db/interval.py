# coding: utf-8
# 间隔时间数据库

from db.base import DBbase

"""
CREATE TABLE `jk_interval` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `interval_time` int(11) DEFAULT 10,
  `interval_type` varchar(200) NOT NULL,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class IntervalDB(DBbase):
    """间隔时间表"""
    def __init__(self):
        super().__init__()

    def get_interval(self):
        interval = self.execute(f'select interval_time,interval_type from jk_interval where is_active=1;', fetch=True)
        return {i[1]: i[0] for i in interval}

    def change_interval(self, interval_type, interval):
        r = self.execute(f'update jk_interval set interval_time={interval} where interval_type="{interval_type}";', commit=True)
        return '修改成功!' if r else '修改失败!'

    def get_interval_by_type(self, _type):
        return self.execute(f'select interval_time from jk_interval where interval_type="{_type}";', fetch=True)[0][0]
