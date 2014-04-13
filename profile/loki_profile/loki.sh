#!/bin/bash
#===============================================================================
#          FILE:  odin.sh
# 
#         USAGE:  ./odin.sh 
# 
#   DESCRIPTION:  
# 
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR:  xiaoliang.zxl (zxl), xiaoliang.zxl@taobao.com
#       COMPANY:  taobao.com
#       VERSION:  1.0
#       CREATED:  04/05/2014 03:33:15 PM CST
#      REVISION:  ---
#===============================================================================

BASE_PATH=$(cd $(dirname $0); pwd)
# DATA_PATH=$(cd $(dirname $0)/data; pwd)
DATA_PATH=$(pwd)
LOG_PATH=$(pwd)

YESTERDAY=$(date -d yesterday +"%Y%m%d")

export YUNTI_INPUT_PATH="/group/tb-taoke-engine/logdata/aitaobao_profile/loki_profile/$YESTERDAY"
# export YUNTI_INPUT_PATH="/group/tb-taoke-engine/logdata/aitaobao_profile/loki_profile/20140405/"

# release
export HADOOP_CONF="/home/ads/hadoop-config"
# export HADOOP_CONF=""
export YUNTI_OUTPUT_PATH="/group/tb-taoke-engine/report/aitaobao_profile/output/"
# debug
#export HADOOP_CONF="/home/jinxi.kj/hadoop-config"
#export YUNTI_OUTPUT_PATH="/group/tb-taoke-engine/dev-test/jinxi.kj/output/$YESTERDAY"
# end

export LOCAL_PATH=$DATA_PATH/output/$YESTERDAY
mkdir -p $LOCAL_PATH

export LANG=C
export JAVA_HOME="/usr/java/jdk1.6.0_13/"
export HADOOP_HOME="/home/hadoop/hadoop-current"
# export HADOOP_HOME="/home/yunti/hadoop-hdfs349745-mr332290-r349744"
export PATH=$PATH:$HADOOP_HOME/bin:$JAVA_HOME/bin:/usr/local/bin:
# export PATH=$PATH:$HADOOP_HOME/bin:/usr/local/bin:
export HDFS_CLUSTER_URI="hdfs://hdpnn:9000"
export HADOOP_EXE="${HADOOP_HOME}/bin/hadoop --config $HADOOP_CONF "
export STREAMING_JAR="$HADOOP_HOME/hadoop-0.19.1-dc-streaming.jar"
export REDUCE_COUNT=1
export HADOOP_CLASSPATH=$HADOOP_CLASSPATH:.

$HADOOP_EXE fs -rmr $YUNTI_OUTPUT_PATH

echo "`date` begin exe hadoop programe on Yunti(BASE_PATH=$BASE_PATH) ..."

$HADOOP_EXE jar $STREAMING_JAR \
    -D mapre.job.name="jinxi_test" \
    -D mapred.reduce.tasks="${REDUCE_COUNT}" \
    -D streaming.inputformat.separator="\n" \
    -D stream.reduce.output.field.separator="\n" \
    -mapper "mapper.py" \
    -reducer "reducer.py" \
    -input $YUNTI_INPUT_PATH \
    -inputformat SequenceFileAsTextInputFormat \
    -output $YUNTI_OUTPUT_PATH \
    -file $BASE_PATH/mapper.py \
    -file $BASE_PATH/reducer.py

ret=$?
if [ $ret -ne 0 ]; then
  echo "`date` failed when execute hadoop programe on Yunti."
  exit -1
fi

rm -rf $LOCAL_PATH

$HADOOP_EXE fs -get "$YUNTI_OUTPUT_PATH" $LOCAL_PATH

$BASE_PATH/sendreport.py --input $LOCAL_PATH/part-00000 --output taobao-ad-tech-taoke-engine@list.alibaba-inc.com --log-path $LOG_PATH/runtime.log
#$BASE_PATH/sendreport.py --input $LOCAL_PATH/part-00000 --output xiaoliang.zxl@taobao.com --log-path $LOG_PATH/runtime.log
