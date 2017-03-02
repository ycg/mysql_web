# -*- coding: utf-8 -*-

import MySQLdb,sys

reload(sys)
sys.setdefaultencoding('utf8')

def table_structure(mysql_structure):
    sql1='/*--user=test;--password=123456;--host=192.168.11.128;--execute=1;--port=3310;*/\
            inception_magic_start;\
            use db1;'
    sql2='inception_magic_commit;'
    sql = sql1 + mysql_structure + sql2
    conn, cur = None, None
    try:
        conn=MySQLdb.connect(host='192.168.11.128',user='root',passwd='',db='',port=6669,use_unicode=True, charset='utf8')
        cur=conn.cursor()
        print(sql)
        ret=cur.execute(sql)
        result=cur.fetchall()
        num_fields = len(cur.description)
        field_names = [i[0] for i in cur.description]
        print field_names
        for row in result:
            print(row)
            #print row[0], "|",row[1],"|",row[2],"|",row[3],"|",row[4],"|",row[5],"|",row[6],"|",row[7],"|",row[8],"|",row[9],"|",row[10]
        #cur.close()
        #conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
    finally:
        if(cur != None):
            cur.close()
        if(conn != None):
            conn.close()
    #return result[1][4].split("\n")

aaa = "CREATE TABLE `iw_static_manifest` (" \
      "  `id` int(20) NOT NULL AUTO_INCREMENT," \
      "  `keyPath` varchar(255) NOT NULL COMMENT '大撒旦撒'," \
      "  `ossUrl` varchar(500) NOT NULL COMMENT ''," \
      "  `version` varchar(20) NOT NULL COMMENT ''," \
      "  `projectId` int(20) NOT NULL COMMENT ''," \
      "  `createTime` datetime NOT NULL," \
      "  `updateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," \
      "  `fileMd5` varchar(40) NOT NULL COMMENT ''," \
      "  PRIMARY KEY (`id`)" \
      ") ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='';"



type = sys.getfilesystemencoding()

table_structure(aaa.decode('UTF-8').encode(type))
