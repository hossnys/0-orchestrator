#install requirments
echo "[*] Installing requirements"
sudo apt-get update
# sudo pip3 install -U git+https://github.com/zero-os/0-orchestrator.git#subdirectory=pyclient
# sudo pip3 install -U git+https://github.com/zero-os/0-core.git#subdirectory=client/py-client

# install jumpscale
echo "[*] Installing Jumpscale"
export SSHKEYNAME=id_rsa
export GIGBRANCH=master
export GIGSAFE=1
export TERM=xterm-256color

export BRANCH=master

curl -s https://raw.githubusercontent.com/Jumpscale/developer/master/jsinit.sh | bash
source ~/.jsenv.sh 
js9_build -l
js9_start

## make controller join zerotier network
echo "[*] Joining zerotier network (controller) ..."
sudo zerotier-one -d || true
sudo zerotier-cli join ${PERF_ZT_NT}; sleep 5

## authorized controller as zerotier member
echo "[*] Authorizing zerotier member (controller) ..."
memberid=$(sudo zerotier-cli info | awk '{print $3}')
curl -H "Content-Type: application/json" -H "Authorization: Bearer ${PERF_ZT_TOKEN}" -X POST -d '{"config": {"authorized": true, "name":"controller"}}' https://my.zerotier.com/api/network/${PERF_ZT_NT}/member/${memberid}


## make js9 container join zerotier network
echo "[*] Joining zerotier network (js9 container) ..."
docker exec -d js9 bash -c "zerotier-one -d" || true; sleep 1
docker exec js9 bash -c "zerotier-cli join ${PERF_ZT_NT}"; sleep 5

## authorized js9 container as zerotier member
echo "[*] Authorizing zerotier member ..."
memberid=$(docker exec js9 bash -c "zerotier-cli info" | awk '{print $3}')
curl -H "Content-Type: application/json" -H "Authorization: Bearer ${PERF_ZT_TOKEN}" -X POST -d '{"config": {"authorized": true, "name":"js9 docker"}}' https://my.zerotier.com/api/network/${PERF_ZT_NT}/member/${memberid}

## install orchestrator
echo "[#] Installing orchestrator ..."
ssh -tA root@localhost -p 2222 "export GIGDIR=~/gig; curl -sL https://raw.githubusercontent.com/zero-os/0-orchestrator/master/scripts/install-orchestrator.sh | bash -s ${TRAVIS_BRANCH} ${PERF_ZT_NT} ${PERF_ZT_TOKEN} ${ITSYOUONLINE_ORG}"

#passing jwt
echo "Enabling JWT..." 
scp -P 2222 /tmp/performance_test/0-orchestrator/tests/performance/js9_docker_script.sh root@localhost:
ssh -tA root@localhost -p 2222 "export ITSYOUONLINE_CL_ID=${ITSYOUONLINE_CL_ID}; export ITSYOUONLINE_CL_SECRET=${ITSYOUONLINE_CL_SECRET}; export ITSYOUONLINE_ORG=${ITSYOUONLINE_ORG}; export BRANCH=${BRANCH}; source js9_docker_script.sh"

jwt=$(ssh -p 2222 -tA root@localhost ays generatetoken --clientid ${ITSYOUONLINE_CL_ID} --clientsecret ${ITSYOUONLINE_CL_SECRET} --organization ${ITSYOUONLINE_ORG} --validity 3600 | grep export)
eval $jwt

python3 /tmp/performance_test/0-orchestrator/tests/performance/execute_perf_script.py --jwt $JWT --zerotierid ${PERF_ZT_NT} --organization ${ITSYOUONLINE_ORG} --branch ${BRANCH} --ipminodes ${PERF_IPMI_IPS} --disktype ${PERF_DISK_TYPE} --servers ${PERF_SERVERS} --vdiskcount ${PERF_VDISK_COUNT} --vdisksize ${PERF_VDISK_SIZE} --vdisktype ${PERF_VDISK_TYPE} --runtime ${PERF_RUNTIME}
