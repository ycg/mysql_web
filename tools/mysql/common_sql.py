# -*- coding: utf-8 -*-

#查看没有主键的表
no_primary_key_sql = """
SELECT DISTINCT
    CONCAT(t.table_schema,'.',t.table_name) as tbl,
    t.engine,
    IF(ISNULL(c.constraint_name),'NOPK','') AS nopk,
    IF(s.index_type = 'FULLTEXT','FULLTEXT','') as ftidx,
    IF(s.index_type = 'SPATIAL','SPATIAL','') as gisidx
FROM information_schema.tables AS t
LEFT JOIN information_schema.key_column_usage AS c ON (t.table_schema = c.constraint_schema AND t.table_name = c.table_name AND c.constraint_name = 'PRIMARY')
LEFT JOIN information_schema.statistics AS s ON (t.table_schema = s.table_schema AND t.table_name = s.table_name AND s.index_type IN ('FULLTEXT','SPATIAL'))
WHERE t.table_schema NOT IN ('information_schema','performance_schema','mysql')
AND t.table_type = 'BASE TABLE' AND (t.engine <> 'InnoDB' OR c.constraint_name IS NULL OR s.index_type IN ('FULLTEXT','SPATIAL'))
ORDER BY t.table_schema,t.table_name;"""
