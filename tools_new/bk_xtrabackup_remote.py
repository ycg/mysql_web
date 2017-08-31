# -*- coding: utf-8 -*-

import os, argparse, sys, time, datetime, subprocess, traceback

# xtrabackup远程流式备份脚本
# 两种流式备份方式：
# 1：xbstream + gzip
# 2：tar + pigz

# xbstream解压方式
# 解压：gunzip /tmp/backup.tar.gz
# 恢复到目录：xbstream -x < backup.tar -C /tmp/mysql

# tar+pigz解压方式
# 两种方式
# unpigz /tmp/backup.tar.gz
# pigz -k /tmp/backup.tar.gz

# 全量备份命令：
# 本地压缩
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | gzip > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# 压缩并复制到远程服务器
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "gzip - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=tar --slave-info --no-timestamp --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "pigz - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"

# 增量备份命令：
# 本地压缩
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir=/data/operatingteam/ --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | gzip > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"
# 压缩并复制到远程服务器
# innobackupex --socket=/mysql/data/mysql.sock --user=yangcg --password='yangcaogui' --stream=xbstream --slave-info --no-timestamp --incremental --incremental-basedir=/data/operatingteam/ --extra-lsndir=/data/operatingteam/ /data/operatingteam/ | ssh root@master "gzip - > /data/operatingteam/`date "+%Y-%m-%d_%H-%M-%S.tar.gz"`"


def full_backup(args):
    pass

def increment_backup(args):
    pass


