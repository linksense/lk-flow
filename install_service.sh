#!/bin/bash
#source /etc/bashrc && source /etc/profile
export LANG=zh_CN.UTF-8
export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:$PATH
export BASENAME=${0##*/}
#export PROJECT_NAME=${BASEPATH##*/}
#export BASEPATH=$(cd `dirname $0`; pwd)
export PROJECT_NAME="lk_flow"
export BASEPATH="/opt/software/$PROJECT_NAME"
export PYTHON_PATH="/opt/virtualenvs/defect_detect/bin"
export DEPLOY_RECORD="1"
export LOGSH=$BASEPATH/install.log 
###################################################
####色打
xecho(){
    echo -e  "$(date +%Y-%m-%d-%H:%M:%S) \e[32;10m>>>$1\e[0m"
}
####判断异常时是否继续
confirm(){
    while true; do
        read -p "信息:~~~~~~~~~~请输入Y或N，是否继续执行~~~~~~~~~~:" yn
        case $yn in
            [Yy]* ) break; ;;
            [Nn]* ) exit 1; ;;
            * ) echo "信息:~~~~~~~~~~无效输入,请输入Y或N~~~~~~~~~~";;
        esac
    done
}
####执行命令状态检测
check_return(){
    if [[ $1 == 0 ]];then
        echo -e "$(date +%Y-%m-%d-%H:%M:%S) \e[32;10m成功:$2\e[0m"
    else
        echo -e "$(date +%Y-%m-%d-%H:%M:%S) \e[31;5m失败:$2\e[0m"
        exit 1
        #confirm
    fi
}

####检查依赖
check_pip(){
    cd $BASEPATH
    if [[ ! -d $BASEPATH ]]; then
        xecho "项目路径不存在：$BASEPATH "
        exit 12;
    fi
    if [[ ! -f $PYTHON_PATH/pip ]]; then
        xecho "检查python虚拟环境不存在：$PYTHON_PATH 请ln软链接合并算法、前后端环境"
        exit 12;
    fi
    ping 114.114.114.114 -W 1 -w 1 -c 3 2>/dev/null|grep -c 'time=.*ms' &> /dev/null
    if [[ $? == 0 ]]; then
        $PYTHON_PATH/pip install --upgrade -r $BASEPATH/lk_requirements.txt -i  https://pypi.douban.com/simple 1>/dev/null
        check_return $? "检查依赖包"
    else
        $PYTHON_PATH/pip install -r lk_requirements.txt --no-index 1>/dev/null
        if [[ "$?" != 0 ]]; then  
            xecho "检查依赖包失败，请向联觉运维人员获取离线依赖包！！！"
            xecho "建议先下载：$BASEPATH/lk_requirements.txt"
            xecho "建议联网下打包：$PYTHON_PATH/pip3.6 download -r lk_requirements.txt -i  https://pypi.douban.com/simple" 
            exit 11; 
        fi
        check_return 0 "检查依赖包"
    fi
}
####安装程序
install_service(){
    cd $BASEPATH ;mkdir -p /var/log/lksense/supervisor
    ${PYTHON_PATH}/pip install -e . --no-index 1>/dev/null
    check_return $? "安装程序"
    [[ ! -f /etc/${PROJECT_NAME}_config.yaml ]] && cp -rpf ${PROJECT_NAME}_config.yaml  /etc/${PROJECT_NAME}_config.yaml && export DEPLOY_RECORD=0
tee /etc/supervisord.d/${PROJECT_NAME}.ini 1>/dev/null << EOOF
[program:lk_flow]
process_name = %(program_name)s
command = $PYTHON_PATH/lk_flow run
directory = /opt/software/lk_flow/
numprocs = 1
autostart = true
autorestart = true
startretries = 3
user = root
redirect_stderr = true
stdout_logfile = /var/log/lksense/supervisor/lk_flow.log
stderr_logfile = /var/log/lksense/supervisor/lk_flow.log
environment = lk_flow_config_path="/etc/lk_flow_config.yaml"
EOOF
}
####DDL
update_db(){
    cd /etc/
    ${PYTHON_PATH}/lk_flow init
    check_return $? "更新初始程序"
}
####检查配置
check_conf(){
    cd $BASEPATH
    conf_file="$1"
    conf_line=$(cat $conf_file |grep -Ev '^#|^$'|awk -F '=' '{print $1}'|awk -F ':' '{print $1}'|xargs -i echo {})
    for line in $conf_line; do
        #echo "检查配置项：$line"
        line=$(echo $line|sed 's#\[#\\[#g'|sed 's#\]#\\]#g')
        cf=$(cat /etc/$conf_file)
        #echo -e "$cf" | grep  "^${line}[ =:]"
        if [[ $(echo -e "$cf" | grep  "^${line}[ =:]"|wc -l) == 0 ]]; then
            if [[ "$line" =~ "[" ]];then
                printf ""
            else
                xecho "配置出错：检查项目$conf_file 在使用的 /etc/$conf_file 缺少配置项:$line 请修复后重启服务"
            fi
        fi
    done
}
####启动
start_service(){
    if [[ $DEPLOY_RECORD == '0' ]]; then
        xecho "第一次部署，配置文件被覆盖，请手动调整配置：/etc/${PROJECT_NAME}_config.yaml"
        #xecho "使用：${PYTHON_PATH}/${PROJECT_NAME} format_tables 更新数据库 "
        xecho "使用：supervisorctl update 更新进程管理"
        xecho "使用：supervisorctl  restart $PROJECT_NAME 启动"
        exit 4;
    fi
    update_db
    supervisorctl update |tee -a $LOGSH
    supervisorctl restart $PROJECT_NAME |tee -a $LOGSH
    sleep 4
    supervisorctl status |tee -a $LOGSH
    supervisorctl status|grep 'RUNNING'|grep -c ${PROJECT_NAME} 1>/dev/null
    check_return $? "启动程序：$PROJECT_NAME"
}
####调用函数
xecho "脚本版本V1.0"
xecho "---->> 部署项目：$PROJECT_NAME 位置：$BASEPATH <<----"
[[ "$1" != "no" ]] && check_pip
install_service
start_service
#check_conf "${PROJECT_NAME}_config.yaml"
