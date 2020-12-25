# coding: utf-8
# 用户数据库

from db.base import DBbase
from util.api import md5
from config import Page

"""
CREATE TABLE `jk_users` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user` varchar(15) DEFAULT NULL,
  `password` varchar(32) DEFAULT NULL,
  `auth` varchar(20) DEFAULT NULL COMMENT 'admin / user',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""


class UserDB(DBbase):
    """管理用户表"""
    def __init__(self):
        super().__init__()

    def is_have_user(self, user):
        """
        :param user: 用户名
        :return:
        """
        base_sql = f'select id from jk_users where user="{user}";'
        return self.execute(base_sql)

    def create_user(self, login_user_id, user, password, auth: str = 'admin'):
        """
        :param user: 用户名
        :param password: 密码
        :param auth: 用户权限 'admin'/'user'
        :return:
        """
        if self.get_auth(login_user_id) == 'admin':
            if not self.is_have_user(user):
                sql = f'insert into jk_users (user,password,auth) values ("{user}","{md5(password)}","{auth}");'
                if self.execute(sql, commit=True):
                    return '添加成功!'
                else:
                    return '添加失败!'
            return '添加失败, 请更换用户名重试!'
        return '您无此权限, 请联系管理员!'

    def get_auth(self, user_id):
        """
        返回当前用户的权限
        :param user_id: 用户id
        :return: 'admin'/'user'
        """
        sql = f'select auth from jk_users where id={user_id};'
        r = self.execute(sql, fetch=True)
        return r[0][0] if r[0] else False

    def del_user(self, login_user_id, del_user_id):
        """
        :param login_user_id: 当前登录用户id
        :param del_user_id: 要删除的用户id
        :return:
        """
        if self.get_auth(login_user_id) == 'admin':
            if login_user_id == del_user_id:
                return '无法删除自己!'
            if self.execute(f'delete from jk_users where id={del_user_id};', commit=True):
                return '成功删除!'
            return '删除失败!'
        return '您无此权限, 请联系管理员!'

    def change_password(self, user_id, new_password):
        """
        :param user_id: 用户id
        :param new_password: 新的密码
        :return:
        """
        sql = f'update jk_users set password="{md5(new_password)}" where id={user_id};'
        return self.execute(sql, commit=True)

    def is_right_password(self, user, password):
        """
        登录接口调用
        :param user: 用户
        :param password: 密码
        :return:
        """
        sql = f'select id from jk_users where user="{user}" and password="{md5(password)}" and is_active=1;'
        _id = self.execute(sql, fetch=True)
        return _id[0][0] if _id else -1

    @staticmethod
    def _handle_query(start, end, user, is_active=1, need_end=True):
        where_sql = f'where is_active={is_active}'
        if start and end:
            where_sql += f' and time>="{start} 00:00:00" and time <="{end} 23:59:59"'
        if user:
            where_sql += f' and user like "%{user}%"'
        return where_sql + ';' if need_end else where_sql

    def get_page(self, start, end, user, limit=Page.user_limit):
        where_sql = self._handle_query(start, end, user)
        db_count = self.execute(f'select count(id) from jk_users {where_sql}', fetch=True)
        page_list = [i + 1 for i in range(db_count[0][0] // limit)]
        page_list = page_list if page_list else [1]
        if db_count[0][0] > limit and (db_count[0][0] % limit != 0):
            page_list.append(page_list[-1] + 1)
        return page_list, db_count[0][0]

    def get_all(self, page, start, end, user, limit=Page.user_limit):
        """
        返回所有用户
        :param user_id: 用户id
        :return:
        """
        where_sql = self._handle_query(start, end, user, need_end=False)
        sql = f'select id,user,auth,create_time,is_active from jk_users {where_sql} limit {page*limit},{limit};'
        rs = self.execute(sql, fetch=True)
        return [{
            "id": r[0],
            "user": r[1],
            "auth": r[2],
            "create_time": r[3].strftime('%Y-%m-%d %H:%M:%S'),
            "is_active": '启用' if r[4] == 1 else '停用'
        } for r in rs] if rs else []
