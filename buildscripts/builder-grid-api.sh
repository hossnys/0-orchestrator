#!/bin/bash
set -e
source $(dirname $0)/tools.sh
ensure_go

branch="master"
echo $1

if [ "$1" != "" ]; then
    branch="$1"
fi

apt-get update
apt-get install -y curl git

git clone -b "${branch}" https://github.com/g8os/grid.git $GOPATH/src/github.com/g8os/grid

cd $GOPATH/src/github.com/g8os/grid/api
go get -v

CGO_ENABLED=0 GOOS=linux go build -a -ldflags '-extldflags "-static"' .

mkdir -p /tmp/archives/
tar -czf "/tmp/archives/grid-api-${branch}.tar.gz" api
