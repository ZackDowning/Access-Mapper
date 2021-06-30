from general import MultiThread
import re
from ipaddress import IPv4Network, IPv4Interface
from pprint import pp


class InterfaceDiscovery:
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


class MACAddressDiscovery:
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


class IPAddressDiscovery:
    """Parses device ARP table to find IP address for provided MAC address"""
    def __init__(self, mac_address, session):
        try:
            self.ip_address = session.send_command(f'show ip arp {mac_address}', use_textfsm=True)[0]['address']
        except IndexError:
            self.ip_address = None
