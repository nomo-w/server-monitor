# coding: utf-8
# 进程数据库

from db.base import DBbase

"""
CREATE TABLE `jk_process` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `machine_id` int(11) NOT NULL,
  `user` varchar(200) NOT NULL,
  `pid` varchar(200) NOT NULL,
  `process_type` varchar(200) NOT NULL,
  `percentage` varchar(100) NOT NULL,
  `process` varchar(200) NOT NULL,
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class ProcessDB(DBbase):
    """进程表"""
    def __init__(self):
        super().__init__()

    def get_process_by_id_and_type(self, mid, _type):
        r = self.execute(f'select user,pid,percentage,process from jk_process where machine_id={mid} and process_type="{_type}" and is_active=1;', fetch=True)
        return [{'user': i[0], 'pid': i[1], 'percentage': i[2], 'process': i[3]} for i in r] if r else []

    def create_process(self, data, mid, _type):
        self.execute(f'delete from jk_process where machine_id={mid} and process_type="{_type}";')
        for i in data:
            self.execute(f'insert into jk_process (machine_id,user,pid,process_type,percentage,process) values '
                         f'({mid},"{i["user"]}",{i["pid"]},"{_type}","{i["%"]}","{i["process"]}");')
        self.commit()
