from ipaddress import IPv4Network

print(str(IPv4Network('192.168.0.0/24').prefixlen))
