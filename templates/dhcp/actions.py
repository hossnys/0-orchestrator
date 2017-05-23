def install(job):
    gateway = job.service.parent.consumers['gateway'][0]
    gwdata = gateway.model.data.to_dict()
    apply_config(job, gwdata)


def apply_config(job, gwdata=None):
    import ipaddress
    from JumpScale.sal.g8os.Container import Container
    from JumpScale.sal.g8os.gateway.dhcp import DHCP

    container = Container.from_ays(job.service.parent)

    gwdata = {} if gwdata is None else gwdata
    nics = gwdata.get('nics', [])
    dhcpservers = []

    for nic in nics:
        dhcpserver = nic.get('dhcpserver')
        if not dhcpserver:
            continue

        cidr = ipaddress.IPv4Interface(nic['config']['cidr'])
        dhcpserver['subnet'] = str(cidr.network)
        dhcpserver['gateway'] = str(cidr.ip)
        dhcpserver['interface'] = nic['name']
        dhcpservers.append(dhcpserver)

    dhcp = DHCP(container, gwdata['domain'], dhcpservers)
    dhcp.apply_config()


def update(job):
    if job.model.args.get("nics", None):
        apply_config(job, job.model.args)
