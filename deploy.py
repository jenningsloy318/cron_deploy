#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Jennings Liu@ 2015-12-03 17:26:04


import paramiko
import subprocess
import socket
import MySQLdb
import argparse
import getpass
import sys
import configparser

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
class connectDB(object):
    def __init__(self,dbserver,dbuser,dbpasswd):
        self.dbserver=dbserver
        self.dbuser=dbuser
        self.dbpasswd=dbpasswd
        self.dbconn=MySQLdb.connect(user=self.dbuser,passwd=self.dbpasswd,host=self.dbserver,port=3308,db='onetool')
        
    def getdoinfo(self,idNUmbertype,idNUmber):
        self.idNUmbertype=idNUmbertype
        self.idNUmber=idNUmber
        self.cursor=self.dbconn.cursor()
        if self.idNUmbertype == 'dp':
            self.query_sql=('''SELECT d.deploy_plan_id,d.id AS 'do_id',l.download_link,cron.id AS 'cron_id', REPLACE(cron.name," ","_")  AS 'cron_name',tc.deploy_path,t.new_version,cs.domain_name,cs.server_ip,c.name AS 'localtion' FROM itt_cron_do d INNER JOIN itt_cron_do_template t ON d.id=t.cron_do_id INNER JOIN itt_template_cpt cpt ON cpt.template_id = t.template_id INNER JOIN ube_package_link l ON l.plan_id = d.deploy_plan_id AND l.template_id = t.template_id  AND l.component_id = cpt.id AND l.build_file_version = t.new_version  INNER JOIN itt_template_cron tc ON tc.template_id = t.template_id INNER JOIN itt_cron cron ON cron.id = tc.cron_id INNER JOIN itt_template_cpt_ts ts ON cpt.id = ts.component_id INNER JOIN itt_cron_server cs ON ts.target_server_id = cs.id LEFT JOIN itt_country c ON cs.country_id = c.id WHERE  d.status = 800  AND d.is_used=1 AND  d.deploy_plan_id='''+self.idNUmber)
        else:
            self.query_sql=(''' SELECT d.deploy_plan_id,d.id AS 'do_id',l.download_link,cron.id AS 'cron_id', REPLACE(cron.name," ","_")  AS 'cron_name',tc.deploy_path,t.new_version,cs.domain_name,cs.server_ip,c.name AS 'localtion' FROM itt_cron_do d INNER JOIN itt_cron_do_template t ON d.id=t.cron_do_id INNER JOIN itt_template_cpt cpt ON cpt.template_id = t.template_id INNER JOIN ube_package_link l ON l.plan_id = d.deploy_plan_id AND l.template_id = t.template_id AND l.component_id = cpt.id AND l.build_file_version = t.new_version  INNER JOIN itt_template_cron tc ON tc.template_id = t.template_id INNER JOIN itt_cron cron ON cron.id = tc.cron_id INNER JOIN itt_template_cpt_ts ts ON cpt.id = ts.component_id INNER JOIN itt_cron_server cs ON ts.target_server_id = cs.id LEFT JOIN itt_country c ON cs.country_id = c.id WHERE d.status=800 AND d.is_used=1 AND  d.id = '''+self.idNUmber)
        self.cursor.execute(self.query_sql)
        data=self.cursor.fetchall()
        self.data_result=[]
        if len(data) != 0:
            for itemid in range(len(data)):
                self.cron_DP=data[itemid][0]
                self.cron_DO=data[itemid][1]
                self.cron_name=data[itemid][4]
                self.cron_mainshell=data[itemid][5]
                self.rpm_name=data[itemid][4]+'-'+str(data[itemid][3])+'-'+str(data[itemid][6])+'.x86_64.rpm'
                self.zip_name=data[itemid][2].split('/')[-1]
                self.rpm_remote='http://ube.synnex.org/building/'+('/').join(data[itemid][2].split('/')[:-1])+'/target/rpm/'+data[itemid][4]+'/RPMS/x86_64/'
                self.zip_remote='http://ube.synnex.org/building/'+data[itemid][2]
                self.cron_server=data[itemid][7]
                self.cron_tuple=(self.cron_DP,self.cron_DO,self.cron_name,self.cron_mainshell,self.rpm_name,self.zip_name,self.rpm_remote,self.zip_remote,self.cron_server)
                self.data_result.append(self.cron_tuple)
                
            return self.data_result
        else:
            return None
    def get_cvs_list(self,donumber):
        self.donumber=donumber
        self.query_sql=('''select a.cron_do_id as 'cron_do_id',d.domain_name  AS 'cron_server' ,CONCAT(b.download_cmd,' ',a.new_version,' ',a.file_path) cvs_url, a.file_path AS 'cvs_file_path'
                from onetool.itt_cron_do_file a  
                inner join onetool.itt_vcs b on a.vcs_id = b.id 
                inner join onetool.itt_cron_do_runtime c  on a.cron_do_id=c.cron_do_id
                inner join itt_cron_server d on d.id=c.cron_server
                where  a.operation in ('NEW','UPDATE') and  a.cron_do_id ='''+self.donumber)
        self.cursor=self.dbconn.cursor()
        self.cursor.execute(self.query_sql)
        data=self.cursor.fetchall()
        self.data_result=[]
        if len(data) != 0:
            for itemid in range(len(data)):
                self.cron_do_id=data[itemid][0]
                self.cron_server=data[itemid][1]
                self.cvs_full_url=data[itemid][2]
                self.cvs_file_path=data[itemid][3]
                self.os_file_path='/'+('/').join(data[itemid][3].split('/')[3:])
                self.cron_do_cvs_list=(self.cron_do_id,self.cron_server,self.cvs_full_url,self.cvs_file_path,self.os_file_path)
                self.data_result.append(self.cron_do_cvs_list)
        
        return self.data_result


if __name__ == "__main__":
    arguments = argparse.ArgumentParser()  
    arguments.add_argument("-u","--user",nargs="?",help="username to login to the cron server",required=True)
    arguments.add_argument("-c","--config",nargs="?",help="DB config file",required=True)
    arguments.add_argument("-i","--install_type",nargs="?",choices=['zip','rpm'],help="installation type zip or rpm",required=True)
    group = arguments.add_mutually_exclusive_group()
    group.add_argument("-dpl","--dplist", nargs="?",help="Comma sperated DP list")
    group.add_argument("-dol","--dolist", nargs="?",help="Comma sperated DO list")
    if len(sys.argv) ==1:
        arguments.print_help()
        sys.exit(1)
    args = arguments.parse_args()
    dp_list = args.dplist
    do_list = args.dolist
    user = args.user
    passwd=getpass.getpass('The '+user+' password for the cron server login: ')
    
    
    config = configparser.ConfigParser()
    configfile=open(args.config)
    config.read_file(configfile)
    onetool_db_server=config['onetool_db']['db_server']
    onetool_db_user=config['onetool_db']['db_user']
    onetool_db_passwd=config['onetool_db']['db_passwd']
    configfile.close()
    
    if do_list:
        cron_operation_list=do_list
        cron_operation_type='do'
    else:
        cron_operation_list=dp_list
        cron_operation_type='dp'
        
    for cron_operation_item in cron_operation_list.split(','):
        db_conn=connectDB(onetool_db_server,onetool_db_user,onetool_db_passwd)
        cronDOs=db_conn.getdoinfo(cron_operation_type,cron_operation_item)
        if cronDOs is not None:
            for cronDOline in range(len(cronDOs)):
                #print(cronDOs[cronDOline])
                cron_DPid=cronDOs[cronDOline][0]
                cron_DOid=cronDOs[cronDOline][1]
                cron_name=cronDOs[cronDOline][2]
                cron_mainshell=cronDOs[cronDOline][3]
                cron_rpm_name=cronDOs[cronDOline][4]
                cron_zip_name=cronDOs[cronDOline][5]
                cron_rpm_remote=cronDOs[cronDOline][6]
                cron_zip_remote=cronDOs[cronDOline][7]
                cron_server=cronDOs[cronDOline][8]
                cron_rpm_full_path=cron_rpm_remote+cron_rpm_name
                cron_zip_home=('/').join(cron_mainshell.split('/')[:-2])+'/'
                cron_mainshell_home=('/').join(cron_mainshell.split('/')[:-1])+'/'
                cron_log_dir=cron_mainshell_home.replace('apps','logs')

                cron_zip_local=('/').join(cron_mainshell.split('/')[:-2])+'/'+cron_zip_name
                cron_acct=cron_mainshell.split('/')[2]
                mkdir_cmd='su - '+cron_acct+' -c "mkdir -p '+cron_zip_home+'"'
                wget_cmd='su - '+cron_acct+' -c "wget '+cron_zip_remote+' -O '+cron_zip_local+'"'
                unzip_cmmd='su - '+cron_acct+' -c "cd '+cron_zip_home+' && unzip -o '+cron_zip_name+'"'
                chmod_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -name "*.sh" |xargs chmod +x"'
                dos2unix_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -type f | xargs dos2unix  "'
                #print(mkdir_cmd,wget_cmd,unzip_cmmd,chmod_cmd,dos2unix_cmd)
                zip_install_cmds=(mkdir_cmd,wget_cmd,unzip_cmmd,chmod_cmd,dos2unix_cmd)
                rpm_install_cmds=('rpm --quiet -q '+cron_name+'&& rpm -Uvh '+cron_rpm_full_path+'||rpm -ivh '+cron_rpm_full_path,)

                if args.install_type.strip()=='zip':
                    cmds=zip_install_cmds
                else:
                    cmds=rpm_install_cmds

                print('Install cronDP-'+str(cron_DPid)+' cronDO-'+str(cron_DOid)+' : '+cron_name+' on '+cron_server+'\n')
                sshlogin=ssh_server(cron_server,user,passwd)
                
                #print(cron_DPid,cron_DOid,cron_name,cron_acct,cron_mainshell,cron_zip_remote,cron_zip_local,cron_rpm_full_path)
                for cmd in cmds:
                    cmdresult=sshlogin.run_cmd(cmd)
                    if cmdresult[0]:
                        print('excute '+cmd+' successfully\n')
                        print(cmdresult[1])
                    else:
                        print('excute '+cmd+' failed\n')
                        print(cmdresult[1])
    
                #print(cmdresult)
                sshlogin.loginoff()
        else:
            print(cron_operation_item+" is already deployed or is a old type cron")
