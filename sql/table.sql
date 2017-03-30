create database mysql_web;

use mysql_web;

#mysql账户信息表
drop table host_infos;
create table host_infos
(
    host_id mediumint unsigned not null auto_increment primary key,
    host varchar(30) not null default '' comment '主机ip地址或主机名',
    port smallint unsigned not null default 3306 comment '端口号',
    user varchar(30) not null default 'root' ,
    password varchar(30) not null default '' comment '密码',
    remark varchar(100) not null default '' comment '备注',
    is_master tinyint not null default 0 comment '是否是主库',
    is_slave tinyint not null default 0 comment '是否是从库',
    master_id mediumint unsigned not null default 0 comment '如果是从库-关联他主库的id',
    is_deleted tinyint not null default 0 comment '删除的将不再监控',
    created_time timestamp not null default current_timestamp,
    modified_time timestamp not null default current_timestamp on update current_timestamp
) comment = 'mysql账户信息' ;

#insert into host_infos (host, port, user, password, remark) values
#("192.168.11.129", 3306, "yangcg", "yangcaogui", "Master"),
#("192.168.11.130", 3306, "yangcg", "yangcaogui", "Slave");
#insert into host_infos (host, port, user, password, remark) values ("192.168.11.128", 3306, "yangcg", "yangcaogui", "Monitor");
#host_info1 = host_info.HoseInfo("192.168.11.129", 3306, "yangcg", "yangcaogui", "Master")
#host_info2 = host_info.HoseInfo("192.168.11.130", 3306, "yangcg", "yangcaogui", "Slave")
#self.__host_infos[host_info1.key] = host_info1
#self.__host_infos[host_info2.key] = host_info2'''

DROP TABLE mysql_status_log;
CREATE TABLE mysql_status_log
(
    id int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL,
    qps MEDIUMINT UNSIGNED NOT NULL,
    tps MEDIUMINT UNSIGNED NOT NULL,
    commit MEDIUMINT UNSIGNED NOT NULL,
    rollback MEDIUMINT UNSIGNED NOT NULL,
    connections MEDIUMINT UNSIGNED NOT NULL,
    thread_count MEDIUMINT UNSIGNED NOT NULL,
    thread_running_count MEDIUMINT UNSIGNED NOT NULL,
    tmp_tables MEDIUMINT UNSIGNED NOT NULL,
    tmp_disk_tables MEDIUMINT UNSIGNED NOT NULL,
    delay_pos INT UNSIGNED NOT NULL DEFAULT 0,
    send_bytes VARCHAR(7) NOT NULL DEFAULT '',
    receive_bytes VARCHAR(7) NOT NULL DEFAULT '',
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql monitor log';

DROP TABLE mysql_enviroment_data;
CREATE TABLE mysql_enviroment_data
(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL ,
    process_list TEXT NOT NULL DEFAULT '',
    innodb_status TEXT NOT NULL DEFAULT '',
    slave_status TEXT NOT NULL DEFAULT '',
    trx_status TEXT NOT NULL DEFAULT '',
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql envirment data';

CREATE TABLE mysql_host_status_log
(
    id int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL,
    cpu SMALLINT UNSIGNED NOT NULL,
    memory SMALLINT UNSIGNED NOT NULL
) COMMENT = 'mysql monitor log';

CREATE TABLE mysql_data_size_for_day
(
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    data_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    index_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows_incr INT UNSIGNED NOT NULL DEFAULT 0,
    auto_increment_incr INT UNSIGNED NOT NULL DEFAULT 0,
    file_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql data size log';

DROP TABLE mysql_data_size_for_day;
CREATE TABLE mysql_data_size_for_day
(
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    data_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    index_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows_incr INT UNSIGNED NOT NULL DEFAULT 0,
    auto_increment_incr INT UNSIGNED NOT NULL DEFAULT 0,
    file_size_incr BIGINT UNSIGNED NOT NULL DEFAULT 0,
    `date` DATE NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE KEY idx_host_id_date(host_id, `date`)
) COMMENT = 'mysql data size log';

DROP TABLE mysql_data_size_log;
CREATE TABLE mysql_data_size_log
(
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    `schema` VARCHAR(50) NOT NULL DEFAULT '',
    table_name VARCHAR(50) NOT NULL DEFAULT '',
    data_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    index_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows INT UNSIGNED NOT NULL DEFAULT 0,
    auto_increment INT UNSIGNED NOT NULL DEFAULT 0,
    file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    diff INT UNSIGNED NOT NULL DEFAULT 0,
    `date` DATE NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql data size log';

#查看历史mysql异常记录的数据信息
DROP TABLE mysql_exception;
CREATE TABLE mysql_exception
(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    exception_type tinyint unsigned not null,
    level TINYINT UNSIGNED NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql exception';

DROP TABLE mysql_exception_log;
CREATE TABLE mysql_exception_log
(
    id INT UNSIGNED NOT NULL PRIMARY KEY,
    log_text TEXT NOT NULL DEFAULT ''
) COMMENT = 'mysql exception log';