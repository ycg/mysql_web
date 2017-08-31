# -*- coding: utf-8 -*-

import os, argparse, sys, time, datetime, subprocess, traceback

# xtrabackup远程流式备份脚本
# 两种流式备份方式：
# 1：xbstream + gzip
# 2：tar + pigz

# xbstream解压方式
# 解压：gunzip /tmp/backup.tar.gz
# 恢复到目录：xbstream -x < backup.tar -C /tmp/mysql

