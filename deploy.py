#!/usr/bin/env python
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
import datetime

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
        
    def getDOinfo(self,do_query_sql_base,query_id):
        self.do_query_sql=do_query_sql_base+str(query_id)
        self.do_cursor=self.dbconn.cursor()
        self.do_cursor.execute(self.do_query_sql)
        data=self.do_cursor.fetchall()
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
                self.rpm_remote='http://ube.example.org:8888/building/'+('/').join(item[2].split('/')[:-1])+'/target/rpm/'+item[4]+'/RPMS/x86_64/'
                self.zip_remote='http://ube.example.org:8888/building/'+item[2]
                self.cron_server=item[7]
                self.cron_account=item[10]
                self.cron_tuple=(self.cron_DP,self.cron_DO,self.cron_name,self.cron_mainshell,self.rpm_name,self.zip_name,self.rpm_remote,self.zip_remote,self.cron_server,self.cron_account)
                self.data_result.append(self.cron_tuple)
                
            return self.data_result
        else:
            return None
    def getDPinfo(self,dp_do_query_sql_base,query_id):
        self.dp_do_query_sql=dp_do_query_sql_base+str(query_id)
        self.dp_do_cursor=self.dbconn.cursor()
        self.dp_do_cursor.execute(self.dp_do_query_sql)
        dolist=self.dp_do_cursor.fetchall()
        if dolist:
            return dolist


def gen_std_cronDO_cmd(CronDO,install_type):
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
    print('Generating deployment commands for cronDO %d on cron server %s :\n'%(cron_DOid,cron_server))

    cron_rpm_full_path=cron_rpm_remote+cron_rpm_name
    cron_zip_home=('/').join(cron_mainshell.split('/')[:-2])+'/'
    cron_mainshell_home=('/').join(cron_mainshell.split('/')[:-1])+'/'
    cron_log_dir=cron_mainshell_home.replace('apps','logs')

    cron_zip_local=('/').join(cron_mainshell.split('/')[:-2])+'/'+cron_zip_name
    mkdir_cmd='su - '+cron_acct+' -c "mkdir -p '+cron_zip_home+'"'
    wget_cmd='su - '+cron_acct+' -c "wget '+cron_zip_remote+' -O '+cron_zip_local+'"'
    unzip_cmd='su - '+cron_acct+' -c "cd '+cron_zip_home+' && unzip -o '+cron_zip_name+'"'
    chmod_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -name \'*.sh\' -print0|xargs -0 chmod +x"'
    dos2unix_cmd='su - '+cron_acct+' -c "find '+cron_mainshell_home+' -type f -regex \'.*\.\(sh\|sql\)\' -print0| xargs -0 dos2unix  "'
    make_logdir_cmd='su - '+cron_acct+' -c " [ ! -d '+cron_log_dir+' ] && mkdir -p '+cron_log_dir+'|| echo log directory already exits "'

    zip_install_cmds=(mkdir_cmd,wget_cmd,unzip_cmd,chmod_cmd,dos2unix_cmd,make_logdir_cmd)
    rpm_install_cmds=('rpm --quiet -q '+cron_name+'&& rpm -Uvh '+cron_rpm_full_path+'||rpm -ivh '+cron_rpm_full_path,)

    if args.install_type.strip()=='zip':
        cmds=zip_install_cmds
    else:
        cmds=rpm_install_cmds
    return cmds


def deploy_std_cronDO(cron_server,user,passwd,cmds,logfile):
    command_status=[]
    sshlogin=ssh_server(cron_server,user,passwd)
    for cmdnum,cmd in enumerate(cmds):
        cmdresult=sshlogin.run_cmd(cmd)
        if cmdresult[0]:
            print('excute %s successfully\n'%cmd)
            print(cmd)
            print(cmdresult[1]+'\n')
            logfile.write('excute %s successfully\n'%cmd)
            logfile.write(cmd)
            logfile.write(cmdresult[1]+'\n')
            command_status.append(0)
        else:
            print('\033[1;31;47mexcute %s failed\033[0m\n'%cmd)
            print(cmd)
            print('\033[1;31;47m %s \033[0m\n'%cmdresult[1])
            logfile.write('\033[1;31;47mexcute %s failed\033[0m\n'%cmd)
            logfile.write(cmd)
            logfile.write('\033[1;31;47m %s \033[0m\n'%cmdresult[1])
            command_status.append(1)
    sshlogin.loginoff()
    if 1 not in command_status:
        return True
    else:
        return False



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
    print("\n")
    if do_list:
        cron_deploy_list=do_list
        cron_deploy_list_type='DO'
    else:
        cron_deploy_list=dp_list
        cron_deploy_list_type='DP'   

## pre-process the config file
    config = configparser.ConfigParser()
    configfile=open(args.config)
    config.read_file(configfile)
    onetool_db_server=config['onetool_db']['db_server']
    onetool_db_user=config['onetool_db']['db_user']
    onetool_db_passwd=config['onetool_db']['db_passwd']
    onetool_db_port=config['onetool_db']['db_port']
    onetool_db_database=config['onetool_db']['db_database']

    if args.r :
        do_query_sql_base=config['query_sql']['do_base_query_sql'].replace('d.status=800 AND','')
    else:
        do_query_sql_base=config['query_sql']['do_base_query_sql']

    if cron_deploy_list_type=='DP':
        if args.r:
            dp_do_query_sql_base=config['query_sql']['dp_do_query_sql'].replace('d.status=800 AND','')
        else:
            dp_do_query_sql_base=config['query_sql']['dp_do_query_sql']
    configfile.close()


##begin to fetch cron info from DB and deploy cron DOs to target servers
    for cron_deploy_item in cron_deploy_list.split(','):
        logfile=open(cron_deploy_item+'.log','w')
        print("Starting to depoy at %s.\n"%datetime.datetime.now())
        logfile.write("Starting to depoy at %s.\n"%datetime.datetime.now())
        db_conn=connectDB(onetool_db_server,onetool_db_port,onetool_db_database,onetool_db_user,onetool_db_passwd)
        if cron_deploy_list_type =='DP':
            print("Fetching DO list for DP %s !\n"%(cron_deploy_item))
            logfile.write("Fetching DO list for DP %s !\n"%(cron_deploy_item))
            cronDOs=db_conn.getDPinfo(dp_do_query_sql_base,cron_deploy_item)
            for (cronDP,cronDO) in cronDOs:
                DP_status=[]
                print("Fetching details of DO %d !\n"%cronDO)
                logfile.write("Fetching details of DO %d !\n"%cronDO)
                cronDOdetails=db_conn.getDOinfo(do_query_sql_base,cronDO)
                if cronDOdetails:
                    DO_status=[]
                    #for cronDOline in range(len(cronDOs)):
                    for cronDOlineNumber,cronDOline in enumerate(cronDOdetails):
                        cron_DPid=cronDOline[0]
                        cron_DOid=cronDOline[1]
                        cron_name=cronDOline[2]
                        cron_server=cronDOline[8]
                        print('Process %dth line of DO %d :\n'%(cronDOlineNumber+1,cronDO))
                        logfile.write('Process %dth line of DO %d :\n'%(cronDOlineNumber+1,cronDO))
                        cmds=gen_std_cronDO_cmd(cronDOline,args.install_type)
                    
                        print('Deploying cron %s(cronDP %d cronDO %d) on %s!\n'%(cron_name,cron_DPid,cron_DOid,cron_server))
                        logfile.write('Deploying cron %s(cronDP %d cronDO %d) on %s!\n'%(cron_name,cron_DPid,cron_DOid,cron_server))
                        if deploy_std_cronDO(cronDOline[8],user,passwd,cmds,logfile):
                            print("CronDO %d is deployed successfully on %s server!\n"%(cron_DOid,cron_server))
                            logfile.write("CronDO %d is deployed successfully on %s server!\n"%(cron_DOid,cron_server))
                            DO_status.append(0)
                        else:
                            print("\033[1;31;47mCronDO %d is deployed failed on %s  server!\033[0m\n"%(cron_DOid,cron_server))
                            logfile.write("CronDO %d is deployed failed on %s  server!\n"%(cron_DOid,cron_server))
                            DO_status.append(1)
                    if 1 not in DO_status:
                        print("CronDO %d is successfully on all servers!\n"%cronDO)
                        logfile.write("CronDO %d is successfully on all servers!\n"%cronDO)
                        DP_status.append(0)
                    else:
                        print("\033[1;31;47mCronDO %d is deployed failed on some of its target  servers!\033[0m\n"%cronDO)
                        logfile.write("CronDO %d is deployed failed on some of its target  servers!\n"%cronDO)
                        DP_status.append(1)
                else:
                    print("\033[1;31;47mCronDO %d is already deployed or is a old type cron!\033[0m\n"%cronDO)
                    logfile.write("CronDO %d is already deployed or is a old type cron!\n"%cronDO)
            if 1 not in DP_status:
                print("CronDP %s is  deployed successfully!\n"%cron_deploy_item)
                logfile.write("CronDP %s is  deployed successfully!\n"%cron_deploy_item)

            else:
                print("\033[1;31;47mNot all DOs in CronDP %s are already deployed successfully!\n"%cron_deploy_item)
                logfile.write("Not all DOs in CronDP %s are already deployed successfully!\n"%cron_deploy_item)
        
        else:
           print("Fetching details of DO %s !\n"%cron_deploy_item)
           logfile.write("Fetching details of DO %s !\n"%cron_deploy_item)
           cronDOdetails=db_conn.getDOinfo(do_query_sql_base,cron_deploy_item)
           if cronDOdetails:
               DO_status=[]
               #for cronDOline in range(len(cronDOs)):
               for cronDOlineNumber,cronDOline in enumerate(cronDOdetails):
                   cron_DPid=cronDOline[0]
                   cron_DOid=cronDOline[1]
                   cron_name=cronDOline[2]
                   cron_server=cronDOline[8]
                   print('Process  %dth line of DO %s :\n'%(cronDOlineNumber+1,cron_deploy_item))
                   logfile.write('Process  %dth line of DO %s :\n'%(cronDOlineNumber+1,cron_deploy_item))
                   cmds=gen_std_cronDO_cmd(cronDOline,args.install_type)
               
                   print('Deploying cron %s(cronDP %d cronDO %d) on %s!\n'%(cron_name,cron_DPid,cron_DOid,cron_server))
                   logfile.write('Deploying cron %s(cronDP %d cronDO %d) on %s!\n'%(cron_name,cron_DPid,cron_DOid,cron_server))
                   if deploy_std_cronDO(cronDOline[8],user,passwd,cmds,logfile):
                       print("CronDO %s is deployed successfully on %s server!\n"%(cron_deploy_item,cron_server))
                       logfile.write("CronDO %s is deployed successfully on %s server!\n"%(cron_deploy_item,cron_server))
                       DO_status.append(0)
                   else:
                       print("\033[1;31;47mCronDO %s is deployed failed on %s  server!\033[0m\n"%(cron_deploy_item,cron_server))
                       logfile.write("CronDO %s is deployed failed on %s  server!\n"%(cron_deploy_item,cron_server))
                       DO_status.append(1)
               if 1 not in DO_status:
                   print("CronDO %s is successfully on all  servers!\n"%cron_deploy_item)
                   logfile.write("CronDO %s is successfully on all  servers!\n"%cron_deploy_item)
               else:
                   print("\033[1;31;47mCronDO %s is deployed failed on some of its target  servers!\033[0m\n"%cron_deploy_item,)
                   logfile.write("CronDO %s is deployed failed on some of its target  servers!\n"%cron_deploy_item)
           else:
               print("\033[1;31;47mCronDO %s is already deployed or is a old type cron!\033[0m\n"%cron_deploy_item)
               logfile.write("CronDO %s is already deployed or is a old type cron!\n"%cron_deploy_item)
        
    
        print("Deployment finished  at %s.\n"%datetime.datetime.now())
        logfile.write("Deployment finished  at %s.\n"%datetime.datetime.now())
    logfile.close()
