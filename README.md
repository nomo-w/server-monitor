# 监控系统


### 环境

Centos7

Mysql 5.7+ 需要开启group by  (Google = TRADITIONAL)
 ~ SET sql_mode ='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION';

### 部署环境

1. Redis
yum install redis -y &&
systemctl enable redis &&
systemctl start redis

2. pythone3.6+
yum update
yum install python36 -y &&
yum install python36-devel -y &&
yum install python36-setuptools -y &&
ln -s /usr/bin/python3.6 /usr/bin/python3 &&
mkdir /usr/local/lib/python3.6/site-packages &&
easy_install-3.6 pip && ln -s /usr/local/bin/pip3 /usr/bin/pip3 &&
ln -s /usr/local/bin/pip3 /usr/bin/pip3

3. python3 插件
~ pip3 install flask pymysql DBUtils redis requests flask-login flask-cors CloudFlare boto3 gunicorn psutil paramiko


### 启动

1. 监控服务器进程
python3 machine_server.py

2. 打开web
python3 web.py  <- 生产环境推荐使用gunicorn  (start.sh就是使用的gunicorn)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
PS: 找不到gunicorn命令的解决办法：
find / -name gunicorn   # 找到了 /usr/local/python3/bin/gunicorn
ln -s /usr/local/bin/gunicorn /usr/bin/gunicorn
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


### DB ->  cmdb.sql

### 业务逻辑

添加服务器的时候可以选择自动部署或者手动部署两种模式,自动部署需要输入服务器的ssh端口和root密码.
程序将自动把对应的文件拷贝到目标服务器,手动部署模式需要自己拷贝对应文件到服务器.
监控的逻辑主要是吧一个小型web服务器部署到被监控机,主监控服务器定期请求被监控机的接口.
如果发现请求失败或者监控数据异常就会自动添加到警报页面.


### 后续开发

后续会添加手机短信和电话报警还有邮件报警功能.
还会添加域名管理功能,支持cloudflare和aws的cloudfront等多种域名商的域名管理.