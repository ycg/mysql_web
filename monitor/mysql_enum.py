import enum

class MySQLBranch(enum.Enum):
    MySQL = 0
    Percona = 1
    Mariadb = 2

class MonitorEnum(enum.Enum):
    mysql = 4
    host = 3
    status = 0
    innodb = 1
    replication = 2