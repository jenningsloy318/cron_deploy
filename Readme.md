Tools to deploy the crontab files
=======================================
>- Py2 and py3 implemention of cron deployment, support zip and rpm deploy method,need a DB config named deploy.conf.
>- cvs deployment version of cron deployment


## the content of the config about DB connection:
```
[onetool_db]
db_server=onetool_db_server
db_user=onetool_db_account
db_passwd=onetool_db_passw
db_port = 3308
db_database= onetool
```

## the content of the config about query sql 
```
[query_sql]
dp_base_query_sql=SELECT d.deploy_plan_id,d.id AS 'do_id',l.download_link,cron.id AS 'cron_id', REPLACE(cron.name," ","_")  AS 'cron_name',tc.deploy_path,t.new_version,cs.domain_name,cs.server_ip,c.name AS 'localtion',ca.name as cron_account FROM itt_cron_do d INNER JOIN itt_cron_do_template t ON d.id=t.cron_do_id INNER JOIN itt_template_cpt cpt ON cpt.template_id = t.template_id INNER JOIN ube_package_link l ON l.plan_id = d.deploy_plan_id AND l.template_id = t.template_id AND l.component_id = cpt.id AND l.build_file_version = t.new_version  INNER JOIN itt_template_cron tc ON tc.template_id = t.template_id INNER JOIN itt_cron cron ON cron.id = tc.cron_id INNER JOIN itt_template_cpt_ts ts ON cpt.id = ts.component_id INNER JOIN itt_cron_server cs ON ts.target_server_id = cs.id INNER JOIN itt_cron_do_runtime cdr on cdr.cron_do_id = d.id  and cdr.cron_server = ts.target_server_id INNER JOIN itt_cron_account ca on ca.id=cdr.cron_account LEFT JOIN itt_country c ON cs.country_id = c.id WHERE d.status=800 AND d.is_used=1 AND  d.deploy_plan_id=

do_base_query_sql=SELECT d.deploy_plan_id,d.id AS 'do_id',l.download_link,cron.id AS 'cron_id', REPLACE(cron.name," ","_")  AS 'cron_name',tc.deploy_path,t.new_version,cs.domain_name,cs.server_ip,c.name AS 'localtion',ca.name as cron_account FROM itt_cron_do d INNER JOIN itt_cron_do_template t ON d.id=t.cron_do_id INNER JOIN itt_template_cpt cpt ON cpt.template_id = t.template_id INNER JOIN ube_package_link l ON l.plan_id = d.deploy_plan_id AND l.template_id = t.template_id AND l.component_id = cpt.id AND l.build_file_version = t.new_version  INNER JOIN itt_template_cron tc ON tc.template_id = t.template_id INNER JOIN itt_cron cron ON cron.id = tc.cron_id INNER JOIN itt_template_cpt_ts ts ON cpt.id = ts.component_id INNER JOIN itt_cron_server cs ON ts.target_server_id = cs.id INNER JOIN itt_cron_do_runtime cdr on cdr.cron_do_id = d.id  and cdr.cron_server = ts.target_server_id INNER JOIN itt_cron_account ca on ca.id=cdr.cron_account LEFT JOIN itt_country c ON cs.country_id = c.id WHERE d.status=800 AND d.is_used=1 AND  d.id =

cvs_query_sql=select f.name as cron_name,e.deploy_plan_id, a.cron_do_id,d.domain_name  AS 'cron_server', g.name as account_name,CONCAT(b.download_cmd,' ',a.new_version,' ',a.file_path) cvs_cmd, a.file_path AS cvs_path,a.operation, c.deploy_path from onetool.itt_cron_do_file a  inner join onetool.itt_vcs b on a.vcs_id = b.id inner join onetool.itt_cron_do_runtime c  on a.cron_do_id=c.cron_do_id inner join itt_cron_server d on d.id=c.cron_server inner join itt_cron_do e on e.id=a.cron_do_id inner join itt_cron f on f.id= e.cron_id inner join itt_cron_account g on g.id = c.cron_account where  a.operation in ('NEW','UPDATE') and  e.status=900 and a.cron_do_id =
```
