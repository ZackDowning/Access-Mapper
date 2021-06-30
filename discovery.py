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
        self.l3_intf = None
        self.mac_address = None
        show_ip_int = session.send_command('show ip interface', use_textfsm=True)
        for intf in show_ip_int:
            for ip_addr, prefix in zip(intf['ipaddr'], intf['mask']):
                intf_ip = f'{ip_addr}/{prefix}'
                intf_network = str(IPv4Interface(intf_ip).network)
                if any(str(host) == ip_address for host in IPv4Network(intf_network).hosts()):
                    self.l3_intf = intf['intf']
        if self.l3_intf is not None:
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
    def __init__(self, discovery_type, mgmt_ip_list, query_value, username, password):
        self.host_vlan = None
        self.host_mac_address = None
        self.host_ip_address = None
        self.connected_device_l3_interface = None
        self.connected_device_interface = None
        self.connected_device_ip_address = None
        self.connected_device_hostname = None
        self.successful_devices = []
        self.failed_devices = []

        def mt(ip):
            conn = Connection(ip, username, password)
            session = conn.session
            if discovery_type == 'Interface':
                intf = Interface(session, query_value)
                if intf.vlan is not None:
                    self.host_vlan = intf.vlan
                    self.connected_device_interface = intf.intf
                    self.host_mac_address = query_value
            if discovery_type == 'MACAddress':
                mac_addr = MACAddress(session, query_value)
                if mac_addr.l3_intf is not None:
                    self.connected_device_l3_interface = mac_addr.l3_intf
                    self.host_mac_address = mac_addr.mac_address
                    self.host_ip_address = query_value
            if discovery_type == 'IPAddress':
                ip_addr = IPAddress(session, query_value).ip_address
                if ip_addr is not None:
                    self.host_ip_address = ip_addr
            if conn.authorization:
                self.successful_devices.append(ip)
            else:
                self.failed_devices.append(ip)

        while True:
            MultiThread(mt, mgmt_ip_list).mt()
            bug = MultiThread(successful_devices=self.successful_devices, failed_devices=self.failed_devices).bug()
            if not bug:
                break
