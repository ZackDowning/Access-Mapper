import re
from ipaddress import IPv4Network, IPv4Interface
from general import Connection, MultiThread


class Interface:
    """Parses device to find vlan and interface of provided MAC Address"""
    def __init__(self, mac_address, session):
        self.vlan = None
        self.intf = None
        intfs = []
        try:
            show_int_sw = session.send_command('show interface switchport', use_textfsm=True)
            if show_int_sw[0].__contains__('switchport'):
                for s_intf in show_int_sw:
                    if s_intf['mode'].__contains__('access'):
                        intfs.append(s_intf['interface'])
            cdp_nei = session.send_command('show cdp neighbor detail', use_textfsm=True)
            for neighbor in cdp_nei:
                if neighbor['capabilities'].__contains__('Trans-Bridge'):
                    full_ap_l_intf = neighbor['local_port']
                    ap_l_intf = str(
                        re.findall(r'\S{2}', full_ap_l_intf)[0]) + str(re.findall(r'\d+\S+', full_ap_l_intf)[0])
                    if all(intf != ap_l_intf for intf in intfs):
                        intfs.append(ap_l_intf)
            for intf in intfs:
                show_mac = session.send_command(f'show mac address-table interface {intf}', use_textfsm=True)
                if type(show_mac) is list:
                    for mac in show_mac:
                        if mac['destination_address'] == mac_address:
                            self.vlan = mac['vlan']
                            self.intf = intf
        except IndexError:
            pass


class MACAddress:
    """Parses device to see if it is routing provided IP Addresses to find MAC Address and L3 Interface"""
    def __init__(self, ip_address, session):
        self.gateway_ip = None
        self.mac_address = None
        show_ip_int = session.send_command('show ip interface', use_textfsm=True)
        for intf in show_ip_int:
            for ip_addr, prefix in zip(intf['ipaddr'], intf['mask']):
                intf_ip = f'{ip_addr}/{prefix}'
                intf_network = str(IPv4Interface(intf_ip).network)
                if any(str(host) == ip_address for host in IPv4Network(intf_network).hosts()):
                    self.gateway_ip = ip_addr
        if self.gateway_ip is not None:
            try:
                self.mac_address = session.send_command(
                    f'show ip arp {ip_address}', use_textfsm=True)[0]['mac']
            except IndexError:
                pass


class IPAddress:
    """Parses device ARP table to find IP address for provided MAC address"""
    def __init__(self, mac_address, session):
        try:
            self.ip_address = session.send_command(f'show ip arp {mac_address}', use_textfsm=True)[0]['address']
        except IndexError:
            self.ip_address = None


class Discovery:
    def __init__(self, input_type, mgmt_ip_list, query_value, username, password):
        self.host_vlan = None
        self.host_mac_address = None
        self.host_ip_address = None
        self.gateway_ip_address = None
        self.connected_device_interface = None
        self.connected_device_mgmt_ip_address = None
        self.connected_device_hostname = None
        self.gateway_mgmt_ip_address = None
        self.gateway_hostname = None
        self.bug = False
        self.successful_devices = []
        self.failed_devices = []
        self.thread_end = False
        self.discovery_end_type = None

        def mt(ip):
            while not self.thread_end:
                try:
                    conn = Connection(ip, username, password)
                    if conn.authorization:
                        session = conn.session
                        self.successful_devices.append(ip)
                        if input_type == 'IP_Address':
                            if self.host_mac_address is None:
                                mac_addr = MACAddress(query_value, session)
                                if mac_addr.gateway_ip is not None:
                                    self.gateway_ip_address = mac_addr.gateway_ip
                                    self.host_mac_address = mac_addr.mac_address
                                    self.host_ip_address = query_value
                                    self.gateway_hostname = conn.hostname
                                    self.gateway_mgmt_ip_address = ip
                                    intf = Interface(self.host_mac_address, session)
                                    if intf.vlan is not None:
                                        self.host_vlan = intf.vlan
                                        self.connected_device_interface = intf.intf
                                        self.connected_device_hostname = conn.hostname
                                        self.connected_device_mgmt_ip_address = ip
                                        self.discovery_end_type = 'end'
                                        self.thread_end = True
                                    else:
                                        self.discovery_end_type = 'cycle_end'
                            else:
                                intf = Interface(self.host_mac_address, session)
                                if intf.vlan is not None:
                                    self.host_vlan = intf.vlan
                                    self.connected_device_interface = intf.intf
                                    self.connected_device_hostname = conn.hostname
                                    self.connected_device_mgmt_ip_address = ip
                                    self.discovery_end_type = 'end'
                                    self.thread_end = True
                        if input_type == 'MAC_Address':
                            if self.host_ip_address is None:
                                ip_addr = IPAddress(query_value, session).ip_address
                                if ip_addr is not None:
                                    self.host_ip_address = ip_addr
                                    mac_addr = MACAddress(self.host_ip_address, session)
                                    if mac_addr.gateway_ip is not None:
                                        self.gateway_ip_address = mac_addr.gateway_ip
                                        self.host_mac_address = mac_addr.mac_address
                                        self.gateway_hostname = conn.hostname
                                        self.gateway_mgmt_ip_address = ip
                                        intf = Interface(self.host_mac_address, session)
                                        if intf.vlan is not None:
                                            self.host_vlan = intf.vlan
                                            self.connected_device_interface = intf.intf
                                            self.connected_device_hostname = conn.hostname
                                            self.connected_device_mgmt_ip_address = ip
                                            self.discovery_end_type = 'end'
                                            self.thread_end = True
                                        else:
                                            self.discovery_end_type = 'cycle_end'
                                    else:
                                        self.discovery_end_type = 'cycle_end'

                            else:
                                if self.host_mac_address is None:
                                    mac_addr = MACAddress(self.host_ip_address, session)
                                    if mac_addr.gateway_ip is not None:
                                        self.gateway_ip_address = mac_addr.gateway_ip
                                        self.host_mac_address = mac_addr.mac_address
                                        self.gateway_hostname = conn.hostname
                                        self.gateway_mgmt_ip_address = ip
                                        intf = Interface(self.host_mac_address, session)
                                        if intf.vlan is not None:
                                            self.host_vlan = intf.vlan
                                            self.connected_device_interface = intf.intf
                                            self.connected_device_hostname = conn.hostname
                                            self.connected_device_mgmt_ip_address = ip
                                            self.discovery_end_type = 'end'
                                            self.thread_end = True
                                        else:
                                            self.discovery_end_type = 'cycle_end'
                                else:
                                    intf = Interface(self.host_mac_address, session)
                                    if intf.vlan is not None:
                                        self.host_vlan = intf.vlan
                                        self.connected_device_interface = intf.intf
                                        self.connected_device_hostname = conn.hostname
                                        self.connected_device_mgmt_ip_address = ip
                                        self.discovery_end_type = 'end'
                                        self.thread_end = True
                    else:
                        self.failed_devices.append(ip)
                except OSError:
                    self.failed_devices.append(ip)
                self.thread_end = True

        while True:
            self.thread_end = False
            self.successful_devices = []
            self.failed_devices = []
            self.discovery_end_type = None
            d = MultiThread(mt, mgmt_ip_list).mt()
            if self.discovery_end_type == 'cycle_end':
                continue
            elif self.discovery_end_type == 'end':
                break
            else:
                self.bug = MultiThread(
                    iterable=d.iterable,
                    successful_devices=self.successful_devices,
                    failed_devices=self.failed_devices
                ).bug()
                if not self.bug:
                    break
