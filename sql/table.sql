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
    password varchar(40) not null default '' comment '密码',
    remark varchar(100) not null default '' comment '备注',
    is_master tinyint not null default 0 comment '是否是主库',
    is_slave tinyint not null default 0 comment '是否是从库',
    master_id mediumint unsigned not null default 0 comment '如果是从库-关联他主库的id',
    ssh_user VARCHAR(20) NOT NULL DEFAULT 'root' COMMENT 'ssh远程执行命令的用户，默认是root',
    ssh_port SMALLINT UNSIGNED NOT NULL DEFAULT 22 COMMENT '用于ssh远程执行的端口',
    ssh_password VARCHAR(100) NOT NULL DEFAULT '' COMMENT '如果不能免密码登录，需要配置密码',
    is_deleted tinyint not null default 0 comment '删除的将不再监控',
    created_time timestamp not null default current_timestamp,
    modified_time timestamp not null default current_timestamp on update current_timestamp,
    UNIQUE KEY idx_host_ip (`host`, `port`) COMMENT 'ip地址和端口号唯一键'
) comment = 'mysql账户信息' CHARSET utf8 ENGINE innodb;

#insert into host_infos (host, port, user, password, remark) values ("192.168.11.128", 3306, "yangcg", "yangcaogui", "Monitor");

DROP TABLE mysql_status_log;
CREATE TABLE mysql_status_log
(
    id int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL,
    qps MEDIUMINT UNSIGNED NOT NULL,
    tps MEDIUMINT UNSIGNED NOT NULL,
    trxs MEDIUMINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '每秒事务数量',
    commit MEDIUMINT UNSIGNED NOT NULL,
    rollback MEDIUMINT UNSIGNED NOT NULL,
    connections MEDIUMINT UNSIGNED NOT NULL,
    thread_count MEDIUMINT UNSIGNED NOT NULL,
    thread_running_count MEDIUMINT UNSIGNED NOT NULL,
    tmp_tables MEDIUMINT UNSIGNED NOT NULL,
    tmp_disk_tables MEDIUMINT UNSIGNED NOT NULL,
    delay_pos INT UNSIGNED NOT NULL DEFAULT 0,
    send_bytes INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '最小单位字节',
    receive_bytes INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '最小单位字节',
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    key idx_hostId_createdTime (`host_id`, `created_time`)
) COMMENT = 'mysql监控日志' CHARSET utf8 ENGINE innodb;

DROP TABLE os_monitor_data;
CREATE TABLE os_monitor_data
(
    id int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '',
    cpu1 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    cpu5 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    cpu15 FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    cpu_user FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    cpu_sys FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    cpu_iowait FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    mysql_cpu FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    mysql_memory FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT '单位百分比%',
    mysql_size SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'mysql数据大小，单位为G',
    io_qps SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '',
    io_tps SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '',
    io_read FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'io每秒读取数据，单位KB',
    io_write FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'io每秒写入数据，单位KB',
    io_util FLOAT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'io使用率，越大说明io越繁忙',
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    key idx_hostId_createdTime (`host_id`, `created_time`)
) COMMENT = 'linux服务器监控日志' CHARSET utf8 ENGINE innodb;

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

DROP TABLE mysql_data_total_size_log;
CREATE TABLE mysql_data_total_size_log
(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    rows_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    data_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    index_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    all_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    file_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    free_t BIGINT UNSIGNED NOT NULL DEFAULT 0,
    table_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    `date` DATE NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    KEY idx_hostId_date(host_id, `date`)
) COMMENT = '数据库大小汇总表';

DROP TABLE mysql_data_size_log;
CREATE TABLE mysql_data_size_log
(
    id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    `schema` VARCHAR(50) NOT NULL DEFAULT '',
    table_name VARCHAR(80) NOT NULL DEFAULT '',
    data_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    index_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    total_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    rows INT UNSIGNED NOT NULL DEFAULT 0,
    auto_increment BIGINT UNSIGNED NOT NULL DEFAULT 0,
    file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
    free_size BIGINT NOT NULL DEFAULT 0,
    `date` DATE NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW(),
    KEY idx_hostId_date(host_id, `date`)
) COMMENT = '数据库表信息汇总表';

#异常记录表
DROP TABLE mysql_exception;
CREATE TABLE mysql_exception
(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT NOT NULL,
    exception_type TINYINT UNSIGNED NOT NULL DEFAULT 0,
    log_type TINYINT UNSIGNED NOT NULL DEFAULT 0,
    level TINYINT UNSIGNED NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT NOW()
) COMMENT = 'mysql exception';

#异常信息详细表
DROP TABLE mysql_exception_log;
CREATE TABLE mysql_exception_log
(
    id INT UNSIGNED NOT NULL PRIMARY KEY,
    log_text MEDIUMTEXT NOT NULL
) COMMENT = 'mysql exception log';

#慢日志和查询日志pt工具对应的表配置
drop TABLE slow_general_log_table_config;
CREATE TABLE slow_general_log_table_config
(
    host_id MEDIUMINT UNSIGNED NOT NULL PRIMARY KEY ,
    slow_log_db VARCHAR(50) NOT NULL DEFAULT '',
    slow_log_table VARCHAR(50) NOT NULL DEFAULT '',
    slow_log_table_history VARCHAR(50) NOT NULL DEFAULT '',
    general_log_db VARCHAR(50) NOT NULL DEFAULT '',
    general_log_table VARCHAR(50) NOT NULL DEFAULT '',
    general_log_table_history VARCHAR(50) NOT NULL DEFAULT '',
    is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    updated_time TIMESTAMP NOT NULL DEFAULT current_timestamp on UPDATE CURRENT_TIMESTAMP
);

#执行sql日志表
CREATE DATABASE backup;
DROP TABLE execute_sql_log;
CREATE TABLE execute_sql_log
(
    id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    host_id MEDIUMINT UNSIGNED NOT NULL,
    is_backup TINYINT UNSIGNED NOT NULL DEFAULT 0,
    backup_name VARCHAR(50) NOT NULL DEFAULT '',
    `sql` TEXT NOT NULL,
    `comment` VARCHAR(100) NOT NULL DEFAULT '',
    created_time TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE mysql_web_user_info
(
    id MEDIUMINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(20) NOT NULL,
    user_password VARCHAR(100) NOT NULL,
    is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT now(),
    updated_time TIMESTAMP NOT NULL DEFAULT current_timestamp on UPDATE CURRENT_TIMESTAMP
);

insert into mysql_web_user_info (user_name, user_password) values("yangcg", md5("yangcaogui"));

-- -----------------------------------------------------------
-- 慢查询配置表
-- 遇到生成的checksum比bigint还要大
-- 字段修改成 checksum varchar(25) not null
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `mysql_slow_query_review`;
CREATE TABLE `mysql_slow_query_review` (
  `id` INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `checksum` VARCHAR(25) NOT NULL,
  `fingerprint` text,
  `sample` mediumtext,
  `first_seen` datetime DEFAULT NULL,
  `last_seen` datetime DEFAULT NULL,
  `reviewed_by` varchar(20) DEFAULT '',
  `reviewed_on` varchar(20) DEFAULT '',
  `reviewed_id` SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `is_reviewed` TINYINT NOT NULL DEFAULT 0,
  `created_time` TIMESTAMP NOT NULL DEFAULT NOW(),
  `modified_time` TIMESTAMP NOT NULL DEFAULT current_timestamp ON UPDATE CURRENT_TIMESTAMP,
  `comments` varchar(200) DEFAULT '' COMMENT '备注',
  UNIQUE KEY (`checksum`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `mysql_slow_query_review_history`;
CREATE TABLE `mysql_slow_query_review_history` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `serverid_max` smallint(4) NOT NULL DEFAULT 0,
  `db_max` varchar(30) DEFAULT NULL,
  `user_max` varchar(30) DEFAULT NULL,
  `checksum` VARCHAR(25) NOT NULL,
  `sample` mediumtext NOT NULL,
  `ts_min` datetime NOT NULL,
  `ts_max` datetime NOT NULL,
  `ts_cnt` float DEFAULT NULL,
  `Query_time_sum` float DEFAULT NULL,
  `Query_time_min` float DEFAULT NULL,
  `Query_time_max` float DEFAULT NULL,
  `Query_time_pct_95` float DEFAULT NULL,
  `Query_time_stddev` float DEFAULT NULL,
  `Query_time_median` float DEFAULT NULL,
  `Lock_time_sum` float DEFAULT NULL,
  `Lock_time_min` float DEFAULT NULL,
  `Lock_time_max` float DEFAULT NULL,
  `Lock_time_pct_95` float DEFAULT NULL,
  `Lock_time_stddev` float DEFAULT NULL,
  `Lock_time_median` float DEFAULT NULL,
  `Rows_sent_sum` float DEFAULT NULL,
  `Rows_sent_min` float DEFAULT NULL,
  `Rows_sent_max` float DEFAULT NULL,
  `Rows_sent_pct_95` float DEFAULT NULL,
  `Rows_sent_stddev` float DEFAULT NULL,
  `Rows_sent_median` float DEFAULT NULL,
  `Rows_examined_sum` float DEFAULT NULL,
  `Rows_examined_min` float DEFAULT NULL,
  `Rows_examined_max` float DEFAULT NULL,
  `Rows_examined_pct_95` float DEFAULT NULL,
  `Rows_examined_stddev` float DEFAULT NULL,
  `Rows_examined_median` float DEFAULT NULL,
  `Rows_affected_sum` float DEFAULT NULL,
  `Rows_affected_min` float DEFAULT NULL,
  `Rows_affected_max` float DEFAULT NULL,
  `Rows_affected_pct_95` float DEFAULT NULL,
  `Rows_affected_stddev` float DEFAULT NULL,
  `Rows_affected_median` float DEFAULT NULL,
  `Rows_read_sum` float DEFAULT NULL,
  `Rows_read_min` float DEFAULT NULL,
  `Rows_read_max` float DEFAULT NULL,
  `Rows_read_pct_95` float DEFAULT NULL,
  `Rows_read_stddev` float DEFAULT NULL,
  `Rows_read_median` float DEFAULT NULL,
  `Merge_passes_sum` float DEFAULT NULL,
  `Merge_passes_min` float DEFAULT NULL,
  `Merge_passes_max` float DEFAULT NULL,
  `Merge_passes_pct_95` float DEFAULT NULL,
  `Merge_passes_stddev` float DEFAULT NULL,
  `Merge_passes_median` float DEFAULT NULL,
  `InnoDB_IO_r_ops_min` float DEFAULT NULL,
  `InnoDB_IO_r_ops_max` float DEFAULT NULL,
  `InnoDB_IO_r_ops_pct_95` float DEFAULT NULL,
  `InnoDB_IO_r_ops_stddev` float DEFAULT NULL,
  `InnoDB_IO_r_ops_median` float DEFAULT NULL,
  `InnoDB_IO_r_bytes_min` float DEFAULT NULL,
  `InnoDB_IO_r_bytes_max` float DEFAULT NULL,
  `InnoDB_IO_r_bytes_pct_95` float DEFAULT NULL,
  `InnoDB_IO_r_bytes_stddev` float DEFAULT NULL,
  `InnoDB_IO_r_bytes_median` float DEFAULT NULL,
  `InnoDB_IO_r_wait_min` float DEFAULT NULL,
  `InnoDB_IO_r_wait_max` float DEFAULT NULL,
  `InnoDB_IO_r_wait_pct_95` float DEFAULT NULL,
  `InnoDB_IO_r_wait_stddev` float DEFAULT NULL,
  `InnoDB_IO_r_wait_median` float DEFAULT NULL,
  `InnoDB_rec_lock_wait_min` float DEFAULT NULL,
  `InnoDB_rec_lock_wait_max` float DEFAULT NULL,
  `InnoDB_rec_lock_wait_pct_95` float DEFAULT NULL,
  `InnoDB_rec_lock_wait_stddev` float DEFAULT NULL,
  `InnoDB_rec_lock_wait_median` float DEFAULT NULL,
  `InnoDB_queue_wait_min` float DEFAULT NULL,
  `InnoDB_queue_wait_max` float DEFAULT NULL,
  `InnoDB_queue_wait_pct_95` float DEFAULT NULL,
  `InnoDB_queue_wait_stddev` float DEFAULT NULL,
  `InnoDB_queue_wait_median` float DEFAULT NULL,
  `InnoDB_pages_distinct_min` float DEFAULT NULL,
  `InnoDB_pages_distinct_max` float DEFAULT NULL,
  `InnoDB_pages_distinct_pct_95` float DEFAULT NULL,
  `InnoDB_pages_distinct_stddev` float DEFAULT NULL,
  `InnoDB_pages_distinct_median` float DEFAULT NULL,
  `QC_Hit_cnt` float DEFAULT NULL,
  `QC_Hit_sum` float DEFAULT NULL,
  `Full_scan_cnt` float DEFAULT NULL,
  `Full_scan_sum` float DEFAULT NULL,
  `Full_join_cnt` float DEFAULT NULL,
  `Full_join_sum` float DEFAULT NULL,
  `Tmp_table_cnt` float DEFAULT NULL,
  `Tmp_table_sum` float DEFAULT NULL,
  `Tmp_table_on_disk_cnt` float DEFAULT NULL,
  `Tmp_table_on_disk_sum` float DEFAULT NULL,
  `Filesort_cnt` float DEFAULT NULL,
  `Filesort_sum` float DEFAULT NULL,
  `Filesort_on_disk_cnt` float DEFAULT NULL,
  `Filesort_on_disk_sum` float DEFAULT NULL,
  `created_time` TIMESTAMP NOT NULL DEFAULT NOW(),
  `modified_time` TIMESTAMP NOT NULL DEFAULT current_timestamp ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_checksum` (`checksum`, serverid_max)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
-- -------------------------------------------------------------------

/*
#统计慢查询频率日志表
drop table mysql_slow_query_log;
CREATE TABLE mysql_slow_query_log
(
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  checksum BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '慢查询sql的checksum值',
  created_time TIMESTAMP NOT NULL DEFAULT NOW() COMMENT '慢查询出现的时间'
) ENGINE=Innodb DEFAULT  CHARSET=utf8 COMMENT '慢查询日志表';

#insert触发器
DROP TRIGGER IF EXISTS insert_trigger;
delimiter $$
CREATE TRIGGER insert_trigger AFTER INSERT ON mysql_web.mysql_slow_query_review FOR EACH ROW
BEGIN
     insert into mysql_web.mysql_slow_query_log(checksum, created_time) values(new.checksum, new.first_seen);
END $$
delimiter ;

#update触发器
DROP TRIGGER IF EXISTS update_trigger;
delimiter $$
CREATE TRIGGER update_trigger AFTER UPDATE ON mysql_web.mysql_slow_query_review FOR EACH ROW
BEGIN
     insert into mysql_web.mysql_slow_query_log(checksum, created_time) values(new.checksum, new.last_seen);
END $$
delimiter ;
*/

CREATE TABLE backup_task
(
  task_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  host_id MEDIUMINT UNSIGNED NOT NULL COMMENT '要备份的机器id',
  name VARCHAR(30) NOT NULL DEFAULT '' COMMENT '备份名称',
  tool TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '备份方式，也就是采用什么工具进行备份',
  mode TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '备份模式，全量还是增量',
  cycle VARCHAR(30) NOT NULL DEFAULT '' COMMENT '备份周期，只有增量的时候才有周期',
  time TIME NOT NULL COMMENT '备份时间，每天什么时候开始备份，不能是白天，起码是凌晨以后',
  save_days MEDIUMINT UNSIGNED NOT NULL COMMENT '备份文件保存天数',
  compress TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '时候压缩，默认不压缩',
  storage_host_id TINYINT UNSIGNED NOT NULL COMMENT '备份文件存储机器',
  directory VARCHAR(100) NOT NULL DEFAULT '' COMMENT '备份目录，很重要',
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '是否删除，也可以说是否被禁用',
  created_time TIMESTAMP NOT NULL DEFAULT now() COMMENT '',
  updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ''
) ENGINE=innodb CHARSET=utf8 COMMENT='备份计划表';

CREATE TABLE backup_log
(
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  task_id INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '备份任务id',
  file VARCHAR(100) NOT NULL DEFAULT '' COMMENT '备份文件名称或者目录名称',
  size BIGINT UNSIGNED NOT NULL COMMENT '备份文件或者目录总大小',
  start_datetime TIMESTAMP NOT NULL COMMENT '备份开始时间',
  stop_datetime TIMESTAMP NOT NULL COMMENT '备份结束时间',
  status TINYINT NOT NULL COMMENT '备份状态，备份进行中，备份成功，备份失败',
  result TEXT COMMENT '存储备份结果，可能要存储xtrabackup的日志',
  created_time TIMESTAMP NOT NULL DEFAULT now() COMMENT '数据插入时间'
) ENGINE=innodb CHARSET=utf8 COMMENT='备份日志表';

INSERT  INTO  backup_log (id, task_id, file, size, start_datetime, stop_datetime, status, result, created_time);


CREATE TABLE table_size_log
(
  id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  host_id MEDIUMINT UNSIGNED NOT NULL COMMENT '主机id',
  db_name VARCHAR(50) NOT NULL DEFAULT '' COMMENT '数据库名称',
  table_name VARCHAR(50) NOT NULL DEFAULT '' COMMENT '表名称',
  data_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '数据大小',
  index_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '索引大小',
  total_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总大小=数据+索引',
  rows INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '行数',
  auto_increment BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '自增长ID',
  file_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小-ibd文件',
  free_size BIGINT NOT NULL DEFAULT 0 COMMENT '数据碎片大小',
  increase_size INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '相比于昨天数据增长的大小=total_szie-total_size(昨天的)',
  `date` DATE NOT NULL COMMENT '数据生成日期',
  created_time TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '行更新时间',
  UNIQUE KEY host_id_date(`host_id`, `date`)
) ENGINE=innodb CHARSET=utf8 COMMENT='表大小日志表';

CREATE TABLE host_all_table_size_log
(
  id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  host_id MEDIUMINT UNSIGNED NOT NULL COMMENT '主机id',
  data_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总数据大小',
  index_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总索引大小',
  total_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总大小=总数据+总索引',
  rows BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总行数',
  file_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总文件大小-ibd文件',
  free_size BIGINT NOT NULL DEFAULT 0 COMMENT '总数据碎片大小',
  increase_size BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '相比于昨天数据增长的大小=total_szie-total_size(昨天的)',
  `date` DATE NOT NULL COMMENT '数据生成日期',
  created_time TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '行更新时间',
  UNIQUE KEY host_id_date(`host_id`, `date`)
) ENGINE=innodb CHARSET=utf8 COMMENT='mysql实例表数据总大小';