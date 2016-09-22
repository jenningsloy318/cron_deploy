#!/bin/bash
cron_file_list=$1
tmproot=/tmp/$LOGNAME
logfile=$cron_file_list.log
fifofile=$cron_file_list.fifo
[[ -p $fifofile ]] || mkfifo $fifofile
cat $fifofile | tee $logfile &
exec 1>$fifofile
exec 2>&1
#if [ "x$cron_file_list"="x" ]; then
# echo "usage : deploy.sh filelist"
# exit
#fi
####### pre process the file list
sed -i '/cvs/!d' $cron_file_list
## checkout files and copy to the dest
while read line
do
[ -d $tmproot ] || mkdir $tmproot
rm -rf $tmproot/cronjob
cd $tmproot
####checkout the file
echo "$line"
$line
####get the file path
cvspath=`echo $line | awk '{print $8}' `
realpath=`echo $cvspath|awk -F "/" '{for(i=4;i<=NF;i++)printf(FS$i);print ""}'`
filelocation=`dirname $realpath`
filename=`basename $realpath`
####create the dir if not exist
[ -d $filelocation ] || mkdir -p $filelocation
#####backup file
[ -f $realpath ] && echo "cp -p $realpath $realpath.`date +%Y%m%d`"
[ -f $realpath ] && cp -p $realpath $realpath.`date +%Y%m%d`
##### copy new file to dest dir
echo "cp $tmproot/$cvspath $realpath"
cp $tmproot/$cvspath $realpath
####if the file is shell, add excute permission ,convert it to unix format
#[  "${filename##*.}" = "sh" ] && chmod u+x $realpath && dos2unix $realpath 
[  "${filename##*.}" = "sh" ] && chmod u+x $realpath 
#[  "${filename##*.}" = "env" ]&& dos2unix $realpath
#[  "${filename##*.}" = "sql" ]&& dos2unix $realpath
#[  "${filename##*.}" = "ini" ]&& dos2unix $realpath
if file $realpath | awk -F: '{print $2}'|grep -q -E "text|script"; then dos2unix $realpath ;fi
####check files
ls -l $realpath*
echo -e "\n"
done < $cron_file_list
[[ -p $fifofile ]] && rm -f $fifofile
