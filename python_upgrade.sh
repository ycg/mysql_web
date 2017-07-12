#! /bin/sh

#python2.6升级到2.7一键安装脚本

echo "---------------1.download python2.7 package-----------------------"
cd /tmp
file_name="Python-2.7.12.tgz"
`rm -rf ${file_name}`
wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz
`tar -zxvf ${file_name}`

echo "--------------------2.build and install---------------------------"
cd Python-2.7.12
./configure
make all
make install
make clean
make distclean

echo "----------------------3.python version---------------------------"
/usr/local/bin/python2.7 -V

echo "----------------------4.modify link------------------------------"
mv /usr/bin/python /usr/bin/python2.6.6
ln -s /usr/local/bin/python2.7 /usr/bin/python

echo "---------------------5.python new version------------------------"
python -V

echo "--------------------6.modify yum config--------------------------"
sed '1/\!\/usr\/bin\/python/\!\/usr\/bin\/python2.6/g' /usr/bin/yum

echo "----------------------success------------------------------------"

#blog
#http://www.cnblogs.com/emanlee/p/6111613.html
