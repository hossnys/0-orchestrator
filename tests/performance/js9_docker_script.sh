sleep 3

JSVERSION=$(js9 "print(j.core.state.versions.get('JumpScale9')[1:])")
ZEROTIERIP=$(ip addr show zt0 | grep -o 'inet [0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+' | grep -o [0-9].*)

# which branch will be used for 0-core
VL=$(git ls-remote --heads https://github.com/zero-os/0-core.git $BRANCH | wc -l)
if [ $VL == 1 ]
then
  CORE0_BRANCH=$BRANCH
else
  CORE0_BRANCH=master
fi

#Generate JWT
echo 'cl_id='${ITSYOUONLINE_CL_ID}
echo 'iyo_client_secret='${ITSYOUONLINE_CL_SECRET}
echo 'itsyouonlineorg='${ITSYOUONLINE_ORG}

jwt=$(ays generatetoken --clientid ${ITSYOUONLINE_CL_ID} --clientsecret ${ITSYOUONLINE_CL_SECRET} --organization ${ITSYOUONLINE_ORG} --validity 3600)
echo 'jwt --> '$jwt

eval $jwt

echo 'JWT='$JWT
echo "JSVERSION="$JSVERSION
echo "CORE0_BRANCH="$core0_branch

cat >  /optvar/cockpit_repos/orchestrator-server/blueprints/configuration.bp << EOL
configuration__main:
  configurations:
  - key: '0-core-version'
    value: '${CORE0_BRANCH}'
  - key: 'js-version'
    value: '${JSVERSION}'
  - key: 'gw-flist'
    value: 'https://hub.gig.tech/gig-official-apps/zero-os-gw-master.flist'
  - key: 'ovs-flist'
    value: 'https://hub.gig.tech/gig-official-apps/ovs-master.flist'
  - key: '0-disk-flist'
    value: 'https://hub.gig.tech/gig-official-apps/0-disk-master.flist'
  - key: 'jwt-token'
    value: '${JWT}'
  - key: 'jwt-key'
    value: 'MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n27MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny66+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv'
EOL

echo ------------
cat /optvar/cockpit_repos/orchestrator-server/blueprints/configuration.bp

cd /optvar/cockpit_repos/orchestrator-server
ays reload 
ays blueprint configuration.bp
ays run create --follow -y

ays blueprint bootstrap.bp
ays run create --follow -y
