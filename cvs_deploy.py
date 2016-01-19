#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Jennings Liu@ 2015-12-03 17:26:04


import paramiko
import subprocess
import socket
import pymysql
import argparse
import getpass
import sys
import configparser
import re

class ssh_server(object):
    def __init__(self,host,user,passwd,port=22):
        self.ip=host
        self.user=user
        self.passwd=passwd
        self.port=port
        try:
            self.sshconn= paramiko.SSHClient()
            self.sshconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sshconn.connect(hostname=self.ip,port=self.port,username=self.user,password=self.passwd,timeout=10)
            print("Login to "+self.ip.rstrip()+" successfully\n")
            #return True
        except paramiko.AuthenticationException:
            print("\033[1;31;47mLogin to "+self.ip.rstrip()+" failed \033[0m\n")
            #return False
        except paramiko.SSHException:
            print("\033[1;31;47mError occurred when connect to"+self.ip.rstrip()+"\033[0m\n")
            #return False
        except socket.error:
            print("\033[1;31;47mSocket error occurred when connect to"+self.ip.rstrip()+" \033[0m\n")
            #return False
        except paramiko.BadHostKeyException:
            print("\033[1;31;47mSSH key error when connect to "+self.ip.rstrip()+" \033[0m\n")
            #return False
    def run_cmd(self,cmd):
        self.cmd=cmd.strip()
        self.stdin, self.stdout, self.stderr = self.sshconn.exec_command(self.cmd)
        if self.stdout.channel.recv_exit_status() == 0:
            #print(('').join(self.stdout.readlines()))
            return True,('').join(self.stdout.readlines())
        else:
            #print(('').join(self.stderr.readlines()+self.stdout.readlines()))
            return False,('').join(self.stderr.readlines()+self.stdout.readlines())
    def loginoff(self):
        self.sshconn.close()
class sftp_server(object):
    def __init__(self,host,user,passwd,port=22):
        self.transport=paramiko.Transport((host,port))
        try:
            self.transport.connect(username=user,password=passwd)
        except paramiko.SSHException: 
            print("Login failed")
        self.sftp=paramiko.SFTPClient.from_transport(self.transport)
    def download(self,remotefile,localfile):
        self.sftp.get(remotefile,localfile)
    def upload(self,remotefile,localfile):
        self.sftp.upload(localfile,remotefile)
    def logoff(self):
        self.sftp.close()

class connectDB(object):
    def __init__(self,dbserver,dbuser,dbpasswd):
        self.dbserver=dbserver
        self.dbuser=dbuser
        self.dbpasswd=dbpasswd
        #self.dbconn=MySQLdb.connect(user=self.dbuser,passwd=self.dbpasswd,host=self.dbserver,port=3308,db='onetool')
        self.dbconn=pymysql.connect(user=self.dbuser,passwd=self.dbpasswd,host=self.dbserver,port=3308,db='onetool')
        
    def getdoinfo(self,query_sql_base,do_id,):
        self.query_sql=query_sql_base+do_id
        print(self.query_sql)
        self.cursor=self.dbconn.cursor()
        self.cursor.execute(self.query_sql)
        data=self.cursor.fetchall()
        self.data_result=[]
        if len(data) != 0:
            for itemid in range(len(data)):
                self.cron_name=data[itemid][0]
                self.cron_DP=data[itemid][1]
                self.cron_DO=data[itemid][2]
                self.cron_server=data[itemid][3]
                self.cron_acct=data[itemid][4]
                self.cron_file_cvs_cmd=data[itemid][5]
                self.cron_file_cvs_path=data[itemid][6]
                self.cron_operation=data[itemid][7]
                self.cron_main_shell=data[itemid][8]
                self.cron_tuple=(self.cron_name,self.cron_DP,self.cron_DO,self.cron_server,self.cron_acct,self.cron_file_cvs_cmd,self.cron_file_cvs_path,self.cron_operation,self.cron_main_shell)
                self.data_result.append(self.cron_tuple)
                
            return self.data_result
        else:
            return None



if __name__ == "__main__":
    arguments = argparse.ArgumentParser()  
    arguments.add_argument("-u","--user",nargs="?",help="username to login to the cron server",required=True)
    arguments.add_argument("-c","--config",nargs="?",help="DB config file",required=True)
    arguments.add_argument("-dol","--dolist", nargs="?",help="Comma sperated DO list")
    if len(sys.argv) ==1:
        arguments.print_help()
        sys.exit(1)
    args = arguments.parse_args()
    cron_deploy_list = args.dolist
    user = args.user
    passwd=getpass.getpass('The '+user+' password for the cron server login: ')

    config = configparser.ConfigParser()
    configfile=open(args.config)
    config.read_file(configfile)
    onetool_db_server=config['onetool_db']['db_server']
    onetool_db_user=config['onetool_db']['db_user']
    onetool_db_passwd=config['onetool_db']['db_passwd']
    query_sql_base=config['query_sql']['cvs_query_sql']
    configfile.close()
        
    for cron_deploy_item in cron_deploy_list.split(','):
        db_conn=connectDB(onetool_db_server,onetool_db_user,onetool_db_passwd)
        cronDOlines=db_conn.getdoinfo(query_sql_base,cron_deploy_item)
        if cronDOlines is not None:
            for cronDOlineID in range(len(cronDOlines)):
                #print(cronDOs[cronDOline])
                cron_name=cronDOlines[cronDOlineID][0]
                cron_DPid=cronDOlines[cronDOlineID][1]
                cron_DOid=cronDOlines[cronDOlineID][2]
                cron_server=cronDOlines[cronDOlineID][3]
                cron_acct=cronDOlines[cronDOlineID][4]
                cron_file_cvs_cmd=cronDOlines[cronDOlineID][5]
                cron_file_cvs_path=cronDOlines[cronDOlineID][6]
                cron_operation=cronDOlines[cronDOlineID][7]
                cron_main_shell=cronDOlines[cronDOlineID][8]
                cron_main_shell_dir=('/').join(cron_main_shell.split('/')[:-1])
                cron_log_dir=cron_main_shell_dir.replace('apps','logs')

               
            
                print(cron_name,cron_DPid,cron_DOid,cron_server,cron_acct,cron_cvs_cmd,cron_operation,cron_main_shell_dir,cron_log_dir)
                print('Install cronDP-'+str(cron_DPid)+' cronDO-'+str(cron_DOid)+' : '+cron_name+' on '+cron_server+'\n')
                #sshlogin=ssh_server(cron_server,user,passwd)
                #
                ##print(cron_DPid,cron_DOid,cron_name,cron_acct,cron_mainshell,cron_zip_remote,cron_zip_local,cron_rpm_full_path)
                #for cmd in cmds:
                #    cmdresult=sshlogin.run_cmd(cmd)
                #    if cmdresult[0]:
                #        print('excute '+cmd+' successfully\n')
                #        print(cmdresult[1])
                #    else:
                #        print('excute '+cmd+' failed\n')
                #        print(cmdresult[1])
    
                ##print(cmdresult)
                #sshlogin.loginoff()
        else:
            print(cron_operation_item+" is already deployed or is a old type cron")
