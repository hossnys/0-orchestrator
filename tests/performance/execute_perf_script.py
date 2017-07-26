from subprocess import Popen, run, PIPE, STDOUT
from zeroos.orchestrator import client as apiclient
import requests, os, sys, argparse, time, configargparse

def execute_script(script):
    process = Popen(script, shell=True, stderr=PIPE, stdout=PIPE)
    for line in process.stdout:
        output = line.decode("utf-8").strip()
        print('  > {}'.format(output))

def execute_command(cmd):
    process = run(cmd, shell=True, stderr=PIPE, stdout=PIPE)
    if process.returncode:
        sys.exit(process.stderr.decode('utf-8'))
    return process.stdout.decode('utf-8').strip()

def update_bootfile(branch, zerotierid, organization):
    content = """
    DEFAULT G8OS-lkrn
    TIMEOUT 100
    PROMPT  1
    IPAPPEND 2
    label G8OS-lkrn
            kernel ipxe.lkrn
            append dhcp && chain https://bootstrap.gig.tech/ipxe/{}/{}/organization={}%20pcie_aspm=off """.format(branch, zerotierid, organization)

    cmd = "cat > /opt/g8-pxeboot/pxeboot/tftpboot/pxelinux.cfg/911boot <<EOF {}\nEOF".format(content)    
    execute_command(cmd)

def restart_node(ipmi_ip):
    cmd = "ipmitool -I lanplus -H {} -U ADMIN -P ADMIN chassis bootdev pxe".format(ipmi_ip)
    execute_command(cmd)
    cmd = "ipmitool -I lanplus -H {} -U ADMIN -P ADMIN chassis power cycle".format(ipmi_ip)
    execute_command(cmd)
        
def get_runnning_nodes(api):
    nodes = api.nodes.ListNodes().json()
    return [node for node in nodes if node['status'] == 'running']

if __name__ == '__main__':
    parser = configargparse.ArgParser(default_config_files=['config.ini'])
    parser.add('--config', is_config_file=True, help='Config file path')
    parser.add("--jwt", required=True, type=str, help='Jwt')
    parser.add("--zerotierid", required=True, type=str, help='Zerotier network id')
    parser.add("--organization", required=True, type=str, help='itsyouonline organization name')
    parser.add("--branch", required=True, type=str, help='branch name')
    parser.add("--ipminodes", required=True, type=str, help='list of node ipmi ips')
    parser.add("--disktype", required=True, type=str, help='Storagecluster disk type')
    parser.add("--servers", required=True, type=int, help='Number of servers to be created in the storagecluster')
    parser.add("--vdiskcount", required=True, type=int, help='Number of vdisks that need to be created')
    parser.add("--vdisksize", required=True, type=int, help='Size of disks in GB')
    parser.add("--vdisktype", required=True, type=str, help='Type of disk, should be: boot, db, cache, tmp')
    parser.add("--runtime", required=True, type=int, help='Time fio should be run')

    options = parser.parse_args()
    jwt = options.jwt.strip()
    zerotierid = options.zerotierid
    organization = options.organization
    branch = options.branch
    ipminodes = options.ipminodes.split(',')
    disktype = options.disktype
    nodesnumber = len(ipminodes)
    vdiskcount = options.vdiskcount
    vdisksize = options.vdisksize    
    runtime = options.runtime
    vdisktype = options.vdisktype
    servers = options.servers

    cmd = "docker exec -t js9 bash -c 'ip -br a show zt0'"
    restapiserver = 'http://{}:8080'.format(execute_command(cmd).split()[2][:-3])
    api = apiclient.APIClient(base_uri=restapiserver)
    api.set_auth_header("Bearer %s" % jwt)

    # update bootfile
    print('[*] Updating bootfile ...')
    update_bootfile(branch, zerotierid, organization)

    # restart nodes
    print('[*] Restarting nodes ...')
    for ipmi_ip in ipminodes:
        restart_node(ipmi_ip)
    
    # wait until nodes be ready
    print('[*] Waiting until nodes be ready ...')
    while True:
        running_nodes = get_runnning_nodes(api)
        if len(running_nodes) == nodesnumber:
            break
        else:
            time.sleep(3)

    
    # execute diskwiper script 
    print('[*] Executing diskwiper script ...')
    nodes_ips = [x['ipaddress'] for x in running_nodes]
    cmd = 'export JWT={}; python3 /tmp/performance_test/0-orchestrator/scripts/diskwiper.py {}'.format(jwt, ' '.join(nodes_ips))
    execute_command(cmd)

    # deploy storagecluster
    print('[*] Deploying storagecluster mycluster ...')
    data = {
            "label": 'mycluster', 
            "servers": servers, 
            "driveType": disktype, 
            "clusterType":"storage",
            "nodes": [x['id'] for x in get_runnning_nodes(api)]
            }
    
    print(data)
    
    try:
        api.storageclusters.DeployNewCluster(data)
    except requests.HTTPError as e:
        print('Error : Response {} - Content: {}'.format(e.response.status_code, e.response.content))
        sys.exit('Error in last step')

    # execute performance script
    print('[*] Executing performance script ...')
    cmd = 'python3 /tmp/performance_test/0-orchestrator/performance/bd-performance.py --orchestratorserver {} --storagecluster mycluster --vdiskCount {} --vdiskSize {} --runtime {} --vdiskType {} --resultDir .'.format(restapiserver, vdiskcount, vdisksize, runtime, vdisktype)    
    execute_command(cmd)

    # print test results
    print('[*] Test results ...')
    cmd = "python3 /tmp/performance_test/0-orchestrator/performance/print_results.py `ls *.json`"
    print(execute_command(cmd))

    # delete mycluster storagecluster
    try:
        api.storageclusters.KillCluster('mycluster')
    except requests.HTTPError as e:
        sys.exit('cannot delete storagecluster mycluster')

