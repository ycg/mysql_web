## mysql monitor web:</br>
安装环境：</br>
1.基于python2.7.11开发的</br>
2.安装MySQL数据库</br>
3.如果要监控OS，需要设置ssh免密码登录</br>
4.安装如下依赖包</br>
>>>> 执行install.sh脚本</br>
5.在setting.py设置MySQL_Host相关账户信息</br>
>>>> MySQL_Host = host_info.HoseInfo(host="192.168.11.128", port=3306, user="yangcg", password="yangcaogui", remark="Monitor")</br>
6.导入sql/table.sql的SQL脚本</br>
7.在mysql_web.host_infos添加MySQL数据库用户</br>
>>>> insert into host_infos (host, port, user, password, remark) values</br>
>>>> ("192.168.11.129", 3306, "yangcg", "yangcaogui", "Master"),</br>
>>>> ("192.168.11.130", 3306, "yangcg", "yangcaogui", "Slave");</br>
8.添加系统登录账号insert into mysql_web.mysql_web_user_info (user_name, user_password)values("yangcaogui", md5("123456"));</br>
9.启动python mysql_web.py runserver</br>
10.如果要监控慢查询还要进行几步配置</br>

## 支持的功能:</br>
1.mysql tps qps table_cache handler监控</br>
2.支持对innodb各种status进行监控</br>
3.支持对show engine innodb status分析</br>
4.支持对复制进行监控</br>
5.支持对表空间进行分析</br>
7.支持对os基本监控</br>
8.支持收集慢查询监控</br>
9.支持对thread进行完整分析</br>
10.支持实时的图标显示</br>
11.支持对数据库用户账号的查询</br>
12.支持登录验证，未登录不允许查看其它任何界面</br>
13.支持半同步复制的实时监控</br>

## 完成的脚本:
1.一键安装数据库脚本</br>
2.使用mysqlbinlog进行binlog的备份脚本</br>
3.支持基于pymysqlreplication的二进制解析脚本</br>
4.支持慢查询收集脚本</br>
5.支持检查表空间脚本</br>
6.基于mysqldump的创建从库脚本</br>

## 待开发的功能:</br>
1.邮件报警功能</br>
·   接下来进行告警界面的开发，可以自定义告警参数</br>
2.监控数据入库形成历史数据</br>
3.登录界面，权限验证</br>
&emsp 2017-4-28完成基本的登录验证，不过用户名和密码写死的</br>
&emsp 接下来考虑用户验证从数据库里读取，不过这个不急</br>
&emsp 2017-05-02完成从数据库进行登录验证，可以在数据库添加多个账户</br>
4.图标界面支持查看历史数据</br>
5.2017-05-15:支持相对完整的慢查询收集和显示功能</br>
6.刚完成半同步复制的监控</br>
7.完成table显示详细信息的改进</br>

## 界面展示:</br>
![image](https://github.com/ycg/mysql_web/blob/master/static/img/111.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/112.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/113.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/114.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/115.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/116.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/117.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/118.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/119.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/120.png)
![image](https://github.com/ycg/mysql_web/blob/master/static/img/121.png)
