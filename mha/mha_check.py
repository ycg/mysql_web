
import os

def stop_mha(mha_config):
    command = "masterha_stop --conf={0}".format(mha_config.conf_path)
    os.system(command)

def start_mha(mha_config):
    command = "masterha_manager --conf={0} --ignore_last_failover".format(mha_config.conf_path)
    os.system(command)

def check_ssh(mha_config):
    command = "masterha_check_ssh --conf={0}".format(mha_config.conf_path)
    os.system(command)

def check_repl(mha_config):
    command = "masterha_check_repl --conf={0}".format(mha_config.conf_path)
    os.system(command)

def check_status(mha_config):
    command = "masterha_check_status --conf={0}".format(mha_config.conf_path)
    os.system(command)

