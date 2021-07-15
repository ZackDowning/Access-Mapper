import time
import re
from ipaddress import IPv4Network, IPv4Interface
from general import Connection, MultiThread, interface_formatter
from address_validator import ipv4

cycle = True


class Interface:
    """Parses device to find VLAN and interface of provided MAC Address\n
    Returns self attributes:\n
    vlan\n
    intf\n
    Defaults = None"""
    def __init__(self, mac_address, session, devicetype):
        global cycle
        self.vlan = None
        self.intf = None
        intfs = []
        while cycle:
            try:
                # Appends active access interfaces to 'intf' set
                show_int_sw = session.send_command('show interface switchport', use_textfsm=True)
                if show_int_sw[0].__contains__('switchport'):

                    def int_sw(s_intf):
                        if s_intf['mode'].__contains__('access'):
                            intfs.append(interface_formatter(s_intf['interface']))
                    # Asyncrononously processes all interfaces from 'show_int_sw' with 'int_sw' function
                    MultiThread(int_sw, show_int_sw).mt()

                # Appends active interfaces with Cisco WAP to 'intf' set
                cdp_nei = session.send_command('show cdp neighbor detail', use_textfsm=True)

                def ap_intf(neighbor):
                    if neighbor['capabilities'].__contains__('Trans-Bridge'):
                        # Formats interface string into same format as default from 'show_int_sw'
                        ap_l_intf = interface_formatter(neighbor['local_port'])
                        # Appends interface to 'intfs' set if it does not already contain it
                        if all(intf != ap_l_intf for intf in intfs):
                            intfs.append(ap_l_intf)
                # Asyncrononously processes all CDP neighbors from 'cdp_nei' with 'ap_intf' function
                MultiThread(ap_intf, cdp_nei).mt()

                # Checks all MAC addresses in CAM table if interface is an access interface and MAC address is equal
                # to input MAC address
                if devicetype == 'cisco_nxos':
                    output = session.send_command(f'show mac address-table | i */').split('\n')
                    show_mac = []
                    for idx, line in enumerate(output):
                        if idx != 0:
                            line_split = re.split(r' +', line)
                            if len(line_split) == 8:
                                show_mac.append({
                                    'destination_port': line_split[7],
                                    'destination_address': line_split[2],
                                    'vlan': line_split[1]
                                })
                else:
                    show_mac = session.send_command(f'show mac address-table', use_textfsm=True)

                def vlan_intf(mac):
                    global cycle
                    # Formats interface string into same format as default from 'show_int_sw'
                    mac_intf = interface_formatter(mac['destination_port'])
                    if mac['destination_address'] == mac_address and any(x == mac_intf for x in intfs):
                        self.vlan = mac['vlan']
                        self.intf = mac_intf
                        cycle = False
                # Asyncrononously processes all MAC addresses from 'show_mac' with 'vlan_intf' function
                MultiThread(vlan_intf, show_mac).mt()
            except IndexError:
                break


class Gateway:
    """Parses device to see if it is routing provided IP Addresses to find MAC Address and L3 Interface\n
    Returns self attributes:\n
    gateway_ip\n
    mac_address\n
    subnet_mask\n
    network\n
    Defaults = None"""
    def __init__(self, ip_address, session, devicetype):
        global cycle
        self.gateway_ip = None
        self.mac_address = None
        self.subnet_mask = None
        self.network = None
        # Checks if any input IP address is within the subnet of any IP interface
        while cycle:
            if devicetype == 'cisco_nxos':
                output = session.send_command('show ip interface').split('\n')
                show_ip_int = []
                for line in output:
                    x = re.split(r' +', line)
                    try:
                        show_ip_int.append({
                            'ipaddr': x[3].strip(','),
                            'network': x[6]
                        })
                    except IndexError:
                        pass
            else:
                show_ip_int = session.send_command('show ip interface', use_textfsm=True)

            def gateway(intf):
                if devicetype == 'cisco_nxos':
                    # Set of all valid IP addresses within interface network
                    intf_network = intf['network']
                    net = IPv4Network(intf_network)
                    valid_hosts = net.hosts()
                    if any(str(host) == ip_address for host in valid_hosts):
                        self.gateway_ip = intf['ipaddr']
                        self.subnet_mask = str(net.netmask)
                        self.network = intf_network
                else:
                    for ip_addr, prefix in zip(intf['ipaddr'], intf['mask']):
                        intf_ip = f'{ip_addr}/{prefix}'
                        # Network ID/Prefix of IP interface
                        intf_network = str(IPv4Interface(intf_ip).network)
                        net = IPv4Network(intf_network)
                        # Set of all valid IP addresses within above network
                        valid_hosts = net.hosts()
                        if any(str(host) == ip_address for host in valid_hosts):
                            self.gateway_ip = ip_addr
                            self.subnet_mask = str(net.netmask)
                            self.network = intf_network
            # Asyncrononously processes all interfaces from 'show_ip_int' with 'gateway' function
            MultiThread(gateway, show_ip_int).mt()

            # Checks ARP table for MAC address if device has IP subnet with valid host IP of input IP address
            if self.gateway_ip is not None:
                try:
                    self.mac_address = session.send_command(f'show ip arp {ip_address}', use_textfsm=True)[0]['mac']
                    cycle = False
                except IndexError:
                    self.mac_address = None
                    self.gateway_ip = None
                    self.subnet_mask = None
                    self.network = None
            break


class IPAddress:
    """Parses device ARP table to find IP address for provided MAC address\n
    Returns self attributes:\n
    ip_address\n
    Default = None"""
    def __init__(self, mac_address, session, devicetype):
        global cycle
        while cycle:
            if devicetype == 'cisco_nxos':
                raw_arp_output = session.send_command(f'show ip arp | i {mac_address}').split('\n')[0]
                try:
                    self.ip_address = re.split(r' +', raw_arp_output)[0]
                    cycle = False
                except (IndexError, TypeError):
                    self.ip_address = None
            else:
                raw_arp_output = session.send_command(f'show ip arp {mac_address}', use_textfsm=True)
                try:
                    self.ip_address = raw_arp_output[0]['address']
                except (IndexError, TypeError):
                    # Formatting if TextFSM does not format correctly
                    if raw_arp_output.__contains__(mac_address):
                        self.ip_address = raw_arp_output.split('\n')[1].split('  ')[1]
                        cycle = False
                    else:
                        self.ip_address = None
            break


class Connectivity:
    """Checks connectivity of list of IP addresses asyncronously and checks for windows frozen code socket bug\n
    Returns self attributes:\n
    successful_devices = [{\n
    'ip'\n
    'hostname'\n
    'con_type'\n
    'device_type'}]\n
    failed_devices = [{\n
    'ip'\n
    'exception'\n
    'connectivitiy'\n
    'authentication'\n
    'authorization'\n}]"""
    def __init__(self, mgmt_ip_list, username, password):
        def check(ip):
            conn = Connection(ip, username, password).check()
            if conn.authorization:
                self.successful_devices.append(
                    {
                        'ip': ip,
                        'hostname': conn.hostname,
                        'con_type': conn.con_type,
                        'device_type': conn.devicetype
                    }
                )
            else:
                self.failed_devices.append(
                    {
                        'ip': ip,
                        'exception': conn.exception,
                        'connectivity': conn.connectivity,
                        'authentication': conn.authentication,
                        'authorization': conn.authorization
                    }
                )

        while True:
            self.successful_devices = []
            self.failed_devices = []
            d = MultiThread(check, mgmt_ip_list).mt()
            bug = MultiThread(
                iterable=d.iterable,
                successful_devices=self.successful_devices,
                failed_devices=self.failed_devices
            ).bug()
            if not bug:
                break
            else:
                time.sleep(7)


class Discovery:
    """Runs asyncronous discovery for attributes below based on input given init attributes\n
    Returns self attributes\n
    host_vlan\n
    host_mac_address\n
    gateway_ip_address\n
    connected_device_interface\n
    connected_device_mgmt_ip_address\n
    connected_device_hostname\n
    gateway_mgmt_ip_address\n
    gateway_hostname\n
    successful_devices = [{\n
    'ip'\n
    'hostname'\n
    'con_type'\n
    'device_type'}]\n
    failed_devices = [{\n
    'ip'\n
    'hostname'\n
    'con_type'\n
    'device_type'\n
    'exception'}]"""
    def __init__(self, query_value, input_type, mgmt_ip_list, username, password):
        global cycle
        self.host_vlan = None
        self.host_mac_address = None
        self.host_ip_address = None
        self.gateway_ip_address = None
        self.connected_device_interface = None
        self.connected_device_mgmt_ip_address = None
        self.connected_device_hostname = None
        self.gateway_mgmt_ip_address = None
        self.gateway_hostname = None
        self.subnet_mask = None
        self.network = None
        self.bug = False
        self.successful_cycle_devices = []

        def gateway_query(device):
            global cycle
            while cycle:
                ip = device['ip']
                device_type = device['device_type']
                con_type = device['con_type']
                connection = Connection(ip, username, password, device_type, con_type).connection()
                if connection.session is None:
                    self.failed_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype,
                            'exception': connection.exception
                        }
                    )
                    self.successful_devices.remove(device)
                else:
                    self.successful_cycle_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype
                        }
                    )
                    gw = Gateway(self.host_ip_address, connection.session, device_type)
                    if gw.gateway_ip is not None:
                        self.gateway_ip_address = gw.gateway_ip
                        self.host_mac_address = gw.mac_address
                        self.gateway_hostname = device['hostname']
                        self.gateway_mgmt_ip_address = ip
                        self.subnet_mask = gw.subnet_mask
                        self.network = gw.network
                    connection.session.disconnect()
                cycle = False

        def intf_vlan_query(device):
            global cycle
            while cycle:
                ip = device['ip']
                device_type = device['device_type']
                con_type = device['con_type']
                connection = Connection(ip, username, password, device_type, con_type).connection()
                if connection.session is None:
                    self.failed_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype,
                            'exception': connection.exception
                        }
                    )
                    self.successful_devices.remove(device)
                else:
                    self.successful_cycle_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype
                        }
                    )
                    intf = Interface(self.host_mac_address, connection.session, device_type)
                    if intf.vlan is not None:
                        self.host_vlan = intf.vlan
                        self.connected_device_interface = intf.intf
                        self.connected_device_hostname = device['hostname']
                        self.connected_device_mgmt_ip_address = ip
                    connection.session.disconnect()
                cycle = False

        def ip_addr_query(device):
            global cycle
            while cycle:
                ip = device['ip']
                device_type = device['device_type']
                con_type = device['con_type']
                connection = Connection(ip, username, password, device_type, con_type).connection()
                if connection.session is None:
                    self.failed_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype,
                            'exception': connection.exception
                        }
                    )
                    self.successful_devices.remove(device)
                else:
                    self.successful_cycle_devices.append(
                        {
                            'ip': ip,
                            'hostname': device['hostname'],
                            'con_type': connection.con_type,
                            'device_type': connection.devicetype
                        }
                    )
                    ip_addr = IPAddress(self.host_mac_address, connection.session, device_type).ip_address
                    if ip_addr is not None:
                        if ipv4(ip_addr):
                            self.host_ip_address = ip_addr
                    connection.session.disconnect()
                cycle = False

        def mt(function):
            global cycle
            while cycle:
                self.successful_cycle_devices = []
                MultiThread(function, self.successful_devices).mt()
                self.bug = MultiThread(
                    iterable=mgmt_ip_list,
                    successful_devices=self.successful_cycle_devices,
                    failed_devices=self.failed_devices
                ).bug()
                if not self.bug:
                    break
                else:
                    # Used for debugging
                    bug_devices = []
                    for device in self.successful_devices:
                        if device['ip'] != any(device1['ip'] for device1 in self.successful_cycle_devices):
                            bug_devices.append(device)

                    time.sleep(7)
                cycle = False

        con_check = Connectivity(mgmt_ip_list, username, password)
        self.successful_devices = con_check.successful_devices
        self.failed_devices = con_check.failed_devices
        if input_type == 'IP_Address':
            self.host_ip_address = query_value
            mt(gateway_query)
            if self.host_mac_address is None:
                self.host_mac_address = 'Not Found. Required for VLAN and switch info.'
            else:
                time.sleep(7)
                cycle = True
                mt(intf_vlan_query)
        if input_type == 'MAC_Address':
            self.host_mac_address = query_value
            mt(ip_addr_query)
            if self.host_ip_address is None:
                self.host_ip_address = 'Not Found. Required for gateway and router info.'
            else:
                time.sleep(7)
                cycle = True
                mt(gateway_query)
            time.sleep(7)
            cycle = True
            mt(intf_vlan_query)
