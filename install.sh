#! /bin/sh

#yum install -y openssl-devel
yum install -y zip unzip python-devel libffi-devel wget gcc sysstat

function install_package()
{
    python setup.py build
    python setup.py install
}

#old setuptools
cd /tmp
file_name="setuptools-0.6c11.tar.gz"
`rm -rf ${file_name}`
wget http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz
`tar zxvf ${file_name}`
cd setuptools-0.6c11
install_package

#pip
cd /tmp
file_name="pip-9.0.1.tar.gz"
`rm -rf ${file_name}`
wget https://pypi.python.org/packages/11/b6/abcb525026a4be042b486df43905d6893fb04f05aac21c32c638e939e447/pip-9.0.1.tar.gz#md5=35f01da33009719497f01a4ba69d63c9
`tar zxvf ${file_name}`
cd pip-9.0.1
install_package

#pip install package
pip install flask flask-login gevent threadpool pymysql DBUtils six packaging appdirs mysql-replication sqlparse

#new setuptools
cd /tmp
file_name="setuptools-35.0.2.zip"
`rm -rf ${file_name}`
wget https://pypi.python.org/packages/88/13/7d560b75334a8e4b4903f537b7e5a1ad9f1a2f1216e2587aaaf91b38c991/setuptools-35.0.2.zip#md5=c368b4970d3ad3eab5afe4ef4dbe2437
`unzip -o ${file_name}`
cd setuptools-35.0.2
install_package
pip install paramiko
