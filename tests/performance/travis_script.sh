if [ "$TRAVIS_EVENT_TYPE" == "cron" ] || [ "$TRAVIS_EVENT_TYPE" == "api" ]
then

    echo "[*] Joining zerotier..."
    sudo zerotier-cli join ${PERF_ZT_NT}

    echo "[*] Authorizing zerotier member"
    memberid=$(sudo zerotier-cli info | awk '{print $3}')
    curl -s -H "Content-Type: application/json" -H "Authorization: Bearer ${PERF_ZT_TOKEN}" -X POST -d '{"config": {"authorized": true, "name":"travis_machine"}}' https://my.zerotier.com/api/network/${PERF_ZT_NT}/member/${memberid} > /dev/null
    
    sleep 30

    sudo sshpass -p "$PERF_CTRL_PASS" ssh -oStrictHostKeyChecking=no $PERF_CTRL_UN@$PERF_CTRL_IP "git clone -b "${TRAVIS_BRANCH}" https://github.com/zero-os/0-orchestrator /tmp/performance_test/0-orchestrator"
    sudo sshpass -p "$PERF_CTRL_PASS" ssh -oStrictHostKeyChecking=no $PERF_CTRL_UN@$PERF_CTRL_IP "export ITSYOUONLINE_CL_ID="${ITSYOUONLINE_CL_ID}"; export ITSYOUONLINE_CL_SECRET="${ITSYOUONLINE_CL_SECRET}"; export ITSYOUONLINE_ORG="${ITSYOUONLINE_ORG}"; export TRAVIS_BRANCH="${TRAVIS_BRANCH}"; export PERF_ZT_NT="${PERF_ZT_NT}"; export PERF_ZT_TOKEN="${PERF_ZT_TOKEN}"; export PERF_IPMI_IPS="${PERF_IPMI_IPS}"; export PERF_DISK_TYPE="${PERF_DISK_TYPE}"; export PERF_SERVERS="${PERF_SERVERS}"; export PERF_VDISK_COUNT="${PERF_VDISK_COUNT}"; export PERF_VDISK_SIZE="${PERF_VDISK_SIZE}"; export PERF_VDISK_TYPE="${PERF_VDISK_TYPE}"; export PERF_RUNTIME="${PERF_RUNTIME}"; bash /tmp/performance_test/0-orchestrator/tests/performance/controller_script.sh"

else
   echo "Not a cron job" 
fi
