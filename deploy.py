#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Jennings Liu@ 2015-12-03 17:26:04


import paramiko
import subprocess
import socket
import argparse
import getpass
import sys
import configparser
import pymysql

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
    def __init__(self,dbserver,port,db,dbuser,dbpasswd):
        self.dbserver=dbserver
        self.dbuser=dbuser
        self.dbpasswd=dbpasswd
        self.dbport=port
        self.db=db
        #self.dbconn=create_engine('mysql://'+self.dbuser+':'+self.dbpasswd+'@'+self.dbserver+':'+self.dbport+'/'+self.db)
        #self.dbconn=MySQLdb.connect(user=self.dbuser,passwd=self.dbpasswd,host=self.dbserver,port=3308,db='onetool')
        self.dbconn=pymysql.connect(user=self.dbuser,passwd=self.dbpasswd,host=self.dbserver,port=int(self.dbport),db=self.db)
        
    def getdoinfo(self,query_sql_base,query_id):
        self.query_sql=query_sql_base+query_id
        self.cursor=self.dbconn.cursor()
        self.cursor.execute(self.query_sql)
        data=self.cursor.fetchall()
        #data=self.dbconn.execute(self.query_sql)
        self.data_result=[]
        if data :
            for itemid,item in enumerate(data):
                self.cron_DP=item[0]
                self.cron_DO=item[1]
                self.cron_name=item[4]
                self.cron_mainshell=item[5]
                self.rpm_name=item[4]+'-'+str(item[3])+'-'+str(item[6])+'.x86_64.rpm'
                self.zip_name=item[2].split('/')[-1]
                self.rpm_remote='http://ube.synnex.org:8888/building/'+('/').join(item[2].split('/')[:-1])+'/target/rpm/'+item[4]+'/RPMS/x86_64/'
                self.zip_remote='http://ube.synnex.org:8888/building/'+item[2]
                self.cron_server=item[7]
                self.cron_account=item[10]
                self.cron_tuple=(self.cron_DP,self.cron_DO,self.cron_name,self.cron_mainshell,self.rpm_name,self.zip_name,self.rpm_remote,self.zip_remote,self.cron_server,self.cron_account)
                self.data_result.append(self.cron_tuple)
                
            return self.data_result
        else:
            return None



if __name__ == "__main__":
    arguments = argparse.ArgumentParser()  
    arguments.add_argument("-u","--user",nargs="?",help="username to login to the cron server",required=True)
    arguments.add_argument("-c","--config",nargs="?",help="DB config file",required=True)
    arguments.add_argument("-i","--install_type",nargs="?",choices=['zip','rpm'],help="installation type zip or rpm",required=True)
    arguments.add_argument("-r",help="re-deploy again",action='store_true')
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
    
    if do_list:
        cron_deploy_list=do_list
        cron_deploy_list_type='do'
    else:
        cron_deploy_list=dp_list
        cron_deploy_list_type='dp'   


    config = configparser.ConfigParser()
    configfile=open(args.config)
    config.read_file(configfile)
    onetool_db_server=config['onetool_db']['db_server']
    onetool_db_user=config['onetool_db']['db_user']
    onetool_db_passwd=config['onetool_db']['db_passwd']
    onetool_db_port=config['onetool_db']['db_port']
    onetool_db_database=config['onetool_db']['db_database']
    if cron_deploy_list_type=='do':
        if args.r :
            query_sql_base=config['query_sql']['do_base_query_sql'].replace('d.status=800 AND','')
        else:
            query_sql_base=config['query_sql']['do_base_query_sql']
    else:
        if args.r:
            query_sql_base=config['query_sql']['dp_base_query_sql'].replace('d.status=800 AND','')
        else:
            query_sql_base=config['query_sql']['dp_base_query_sql']
    configfile.close()



    for cron_deploy_item in cron_deploy_list.split(','):
        logfile=open(cron_deploy_item+'.log','w')
        print('Fetch the DO/DP %s information from database .\n'%cron_deploy_item)
        logfile.write('Fetch the DO/DP %s information from database .'%cron_deploy_item)
        db_conn=connectDB(onetool_db_server,onetool_db_port,onetool_db_database,onetool_db_user,onetool_db_passwd)
        cronDOs=db_conn.getdoinfo(query_sql_base,cron_deploy_item)
        if cronDOs :
            #for cronDOline in range(len(cronDOs)):
            for cronDOlineNumber,cronDOline in enumerate(cronDOs):
                #print(cronDOs[cronDOline])
                print('Process the %d line :\n'%(cronDOlineNumber+1))
                cron_DPid=cronDOline[0]
                cron_DOid=cronDOline[1]
                cron_name=cronDOline[2]
                cron_mainshell=cronDOline[3]
                cron_rpm_name=cronDOline[4]
                cron_zip_name=cronDOline[5]
                cron_rpm_remote=cronDOline[6]
                cron_zip_remote=cronDOline[7]
                cron_server=cronDOline[8]
                cron_acct=cronDOline[9]
                cron_rpm_full_path=cron_rpm_remote+cron_rpm_name
                cron_zip_home=('/').join(cron_mainshell.split('/')[:-2])+'/'
                cron_mainshell_home=('/').join(cron_mainshell.split('/')[:-1])+'/'
                cron_log_dir=cron_mainshell_home.replace('apps','logs')

                cron_zip_local=('/').join(cron_mainshell.split('/')[:-2])+'/'+cron_zip_name
                mkdir_cmd='su - '+cron_acct+' -c "mkdir -p '+cron_zip_home+'"'
                wget_cmd='su - '+cron_acct+' -c "wget '+cron_zip_remote+' -O '+cron_zip_local+'"'
                unzip_cmd='su - '+cron_acct+' -c "cd '+cron_zip_home+' && unzip -o '+cron_zip_name+'"'
                chmod_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -name "*.sh" -print0|xargs -0 chmod +x"'
                dos2unix_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -type f -name "*.sh" -print0| xargs -0 dos2unix  "'
                make_logdir_cmd='su - '+cron_acct+' -c " [ ! -d '+cron_log_dir+' ] && mkdir -p '+cron_log_dir+'|| echo log directory already exits "'

                zip_install_cmds=(mkdir_cmd,wget_cmd,unzip_cmd,chmod_cmd,dos2unix_cmd,make_logdir_cmd)
                rpm_install_cmds=('rpm --quiet -q '+cron_name+'&& rpm -Uvh '+cron_rpm_full_path+'||rpm -ivh '+cron_rpm_full_path,)

                if args.install_type.strip()=='zip':
                    cmds=zip_install_cmds
                else:
                    cmds=rpm_install_cmds
                #print(cmds)

                print('Install cronDP-'+str(cron_DPid)+' cronDO-'+str(cron_DOid)+' : '+cron_name+' on '+cron_server+'\n')
                logfile.write('Install cronDP-'+str(cron_DPid)+' cronDO-'+str(cron_DOid)+' : '+cron_name+' on '+cron_server+'\n')
                sshlogin=ssh_server(cron_server,user,passwd)
                for cmd in cmds:
                    cmdresult=sshlogin.run_cmd(cmd)
                    if cmdresult[0]:
                        print('excute %s successfully\n'%cmd)
                        logfile.write('excute %s successfully\n'%cmd)
                        print(cmd)
                        logfile.write(cmd+'\n')
                        print(cmdresult[1]+'\n')
                        logfile.write(cmdresult[1]+'\n')
                        logfile.flush()
                    else:
                        print('\033[1;31;47mexcute %s failed\033[0m\n'%cmd)
                        logfile.write('excute command %s failed\n'%cmd)
                        print(cmd)
                        logfile.write(cmd+'\n')
                        print('\033[1;31;47m %s \033[0m\n'%cmdresult[1])
                        logfile.write(cmdresult[1]+'\n')
                        logfile.flush()
    
                #print(cmdresult)
                sshlogin.loginoff()
        else:
            print(cron_deploy_item+" is already deployed or is a old type cron")
        logfile.close()
