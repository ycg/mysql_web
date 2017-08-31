#!/usr/bin/env bash

user="root"
password=""
to_email="ycg166911@163.com"
new_master=$(echo $2 | cut -d = -f 2)
orig_master=$(echo $1 | cut  -d = -f 2)
text="${orig_master} is down, new master is ${new_master}"

mysql -u${user} -p${password} -h${new_master} -e"select HOST from information_schema.processlist where USER='repl'" 2> /dev/null | cut -d : -f 1 | sed 1d > slave_host.txt

while read host_name
do
	rpl_master_ip=$(mysql -u${user} -p${password} -h${host_name} -e"show slave status\G" 2> /dev/null | grep -i Master_Host | awk '{print $2}')
	if [ "${rpl_master_ip}" != "${new_master}" ]; then
		message="${message}${host_name}replication source exception\n"
	else
		message="${message}${host_name}replication master ip is ${rpl_master_ip}\n" ;
	fi

	slave_status=$(mysql -u${user} -p${password} -h${host_name}  -e"show global status like 'Slave_running'" 2>/dev/null | grep -i "Slave_running" | awk '{print $2}')
	if [ "${slave_status}" == "off" ]; then
		message="${message}slave status is OFF\n"
	else
		message="${message}slave status is ON\n"
	fi
done < slave_host.txt

echo -e "${text}\n${message}" | mail -s "mha failover report"  "${to_email}"
echo -e "${text}\n${message}"
echo "successfull send mail!!"
