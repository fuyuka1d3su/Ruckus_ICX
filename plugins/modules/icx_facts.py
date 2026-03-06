#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: icx_facts
author: "Ruckus Wireless (@Commscope)"
short_description: Collect facts from remote Ruckus ICX 7000 series switches
description:
  - Collects a base set of device facts from a remote device that
    is running ICX.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>). The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(!) to specify that a specific subset should
        not be collected.
    required: false
    type: list
    default: '!config'
'''

EXAMPLES = """
- name: Collect all facts from the device
  commscope.icx.icx_facts:
    gather_subset: all
- name: Collect only the config and default facts
  commscope.icx.icx_facts:
    gather_subset:
      - config
- name: Do not collect hardware facts
  commscope.icx.icx_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
# default
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: str
ansible_net_stacked_models:
  description: The model names of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list
ansible_net_stacked_serialnums:
  description: The serial numbers of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list
# hardware
ansible_net_filesystems:
  description: All file system names available on the device
  returned: when hardware is configured
  type: list
ansible_net_filesystems_info:
  description: A hash of all file systems containing info about each file system (e.g. free and total space)
  returned: when hardware is configured
  type: dict
ansible_net_memfree_kb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int
# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: str
# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""


import re
from ansible_collections.commscope.icx.plugins.module_utils.network.icx.icx import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd)


class Default(FactsBase):

    COMMANDS = ['show running-config | include hostname', 'show version', 'show stack']

    def populate(self):
        super(Default, self).run(['skip'])
        super(Default, self).populate()
        data = self.responses[2]
        det = dict()
        if data:
            det = self.parse_unit(data)

        data = self.responses[1]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['model'] = self.parse_model(data)
            self.facts['image'] = self.parse_image(data)
            self.facts['hostname'] = self.parse_hostname(self.responses[0])
            unit = det.get('Unit') or self.parse_primary_unit(data)
            model = det.get('model') or self.facts.get('model')
            serial = self.parse_serialnum(data, unit)
            if serial:
                self.facts['serialnum'] = serial

            if unit:
                info = 'Unit' + unit
                if model:
                    info += ':' + model
                if serial:
                    info += ', ' + serial
            else:
                info = ', '.join([v for v in [model, serial] if v])

            if info:
                self.facts['info'] = info
            self.parse_stacks(data)

    def parse_serialnum(self, data, unit=None):
        if unit:
            match = re.search(r'UNIT\s+%s: SL .*?Serial\s+#:\s*(\S+)' % re.escape(unit), data, re.DOTALL | re.M)
            if match:
                return match.group(1)

        for pattern in [r'^System [Ss]erial [Nn]umber\s*:\s*(\S+)', r'Serial\s+#:\s*(\S+)']:
            match = re.search(pattern, data, re.M)
            if match:
                return match.group(1)

        return ""

    def parse_version(self, data):
        match = re.search(r'SW:\s+Version\s+([^\s,]+)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^hostname (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'^\s*HW:\s+(.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'\([0-9]+ bytes\) from \S+ (\S+)', data)
        if match:
            return match.group(1)

    def parse_unit(self, data):
        match = re.search(r'^\s*(\d+)\s{2,}(\S+)\s{2,}(active|alone)\b', data, re.M | re.I)
        if match:
            return {'Unit': match.group(1), 'model': match.group(2)}

        match = re.search(r'UNIT\s+(\d+):\s+SL\s+\d+:\s+(\S+)', data, re.M | re.I)
        if match:
            return {'Unit': match.group(1), 'model': match.group(2)}

        return dict()

    def parse_primary_unit(self, data):
        match = re.search(r'UNIT\s+(\d+):\s+SL\s+\d+:', data, re.M | re.I)
        if match:
            return match.group(1)

        return ""

    def parse_stacks(self, data):
        match = re.findall(r'UNIT [1-9]+: SL [1-9]+: (\S+)', data, re.M | re.I)
        if match:
            self.facts['stacked_models'] = match

        match = re.findall(r'Serial\s+#:\s*(\S+)', data, re.M)
        if not match:
            match = re.findall(r'^System [Ss]erial [Nn]umber\s*:\s*(\S+)', data, re.M)
        if match:
            self.facts['stacked_serialnums'] = match


class Hardware(FactsBase):

    COMMANDS = [
        'show memory',
        'show flash'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)
            self.facts['filesystems_info'] = self.parse_filesystems_info(self.responses[1])

        if data:
            if 'Invalid input detected' in data:
                warnings.append('Unable to gather memory statistics')
            else:
                match = re.findall(r'Stack unit ([0-9]+):\nTotal DRAM: ([0-9]+) bytes\n  Dynamic memory: ([0-9]+) bytes total, ([0-9]+) bytes free, ([0-9]+%) used', data, re.DOTALL)
                if match:
                    self.facts['memtotal_kb'] = dict()
                    self.facts['memfree_kb'] = dict()
                    for i in range(len(match)):
                        self.facts['memtotal_kb']["Stack Unit " + str(match[i][0])] = {"Total Memory": str(int(match[i][1]) / 1024) + "kb"}
                        self.facts['memfree_kb']["Stack Unit " + str(match[i][0])] = {"Free Memory": str(int(match[i][3]) / 1024) + "kb"}

    def parse_filesystems(self, data):
        return "flash"

    def parse_filesystems_info(self, data):
        facts = dict()
        fs = ''
        for line in data.split('\n'):
            match = re.match(r'^(Stack unit \S+):', line)
            if match:
                fs = match.group(1)
                facts[fs] = dict()
                continue
            match = re.match(r'\W+NAND Type: Micron NAND (\S+)', line)
            if match:
                facts[fs]['spacetotal'] = match.group(1)
            match = re.match(r'\W+Code Flash Free Space = (\S+)', line)
            if match:
                facts[fs]['spacefree'] = int(int(match.group(1)) / 1024)
                facts[fs]['spacefree'] = str(facts[fs]['spacefree']) + "Kb"
        return {"flash": facts}


class Config(FactsBase):

    COMMANDS = ['skip', 'show running-config']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[1]
        if data:
            self.facts['config'] = data


class Interfaces(FactsBase):

    COMMANDS = [
        'skip',
        'show interfaces',
        'show running-config',
        'show lldp',
        'show media'
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['all_ipv4_addresses'] = list()
        self.facts['all_ipv6_addresses'] = list()
        data = self.responses[1]
        if data:
            interfaces = self.parse_interfaces(data)
            self.facts['interfaces'] = self.populate_interfaces(interfaces)

        data = self.responses[1]
        if data:
            data = self.parse_interfaces(data)
            self.populate_ipv4_interfaces(data)

        data = self.responses[2]
        if data:
            self.populate_ipv6_interfaces(data)

        data = self.responses[3]
        lldp_errs = ['Invalid input', 'LLDP is not enabled']

        if data and not any(err in data for err in lldp_errs):
            neighbors = self.run(['show lldp neighbors detail'])
            if neighbors:
                self.facts['neighbors'] = self.parse_neighbors(neighbors[0])

        data = self.responses[4]
        self.populate_mediatype(data)

        interfaceList = {}
        for iface in self.facts['interfaces']:
            if 'type' in self.facts['interfaces'][iface]:
                newName = self.facts['interfaces'][iface]['type'] + iface
            else:
                newName = iface
            interfaceList[newName] = self.facts['interfaces'][iface]
        self.facts['interfaces'] = interfaceList

    def populate_mediatype(self, data):
        lines = data.split("\n")
        for line in lines:
            match = re.match(r'Port (\S+):\W+Type\W+:\W+(.*)', line)
            if match:
                self.facts['interfaces'][match.group(1)]["mediatype"] = match.group(2)

    def populate_interfaces(self, interfaces):
        facts = dict()
        for key, value in iteritems(interfaces):
            intf = dict()
            intf['description'] = self.parse_description(value)
            intf['macaddress'] = self.parse_macaddress(value)
            intf['mtu'] = self.parse_mtu(value)
            intf['bandwidth'] = self.parse_bandwidth(value)
            intf['duplex'] = self.parse_duplex(value)
            intf['lineprotocol'] = self.parse_lineprotocol(value)
            intf['operstatus'] = self.parse_operstatus(value)
            intf['type'] = self.parse_type(value)
            facts[key] = intf
        return facts

    def populate_ipv4_interfaces(self, data):
        for key, value in data.items():
            self.facts['interfaces'][key]['ipv4'] = dict()
            primary_address = addresses = []
            primary_address = re.findall(r'Internet address is (\S+/\S+), .*$', value, re.M)
            addresses = re.findall(r'Secondary address (.+)$', value, re.M)
            if len(primary_address) == 0:
                continue
            addresses.append(primary_address[0])
            for address in addresses:
                addr, subnet = address.split("/")
                ipv4 = dict(address=addr.strip(), subnet=subnet.strip())
                self.add_ip_address(addr.strip(), 'ipv4', key)
                self.facts['interfaces'][key]['ipv4'] = ipv4

    def populate_ipv6_interfaces(self, data):
        parts = data.split("\n")
        key = None
        interface_type = None
        for line in parts:
            match = re.match(r'\W*interface (\S+) (\S+)', line)
            if match:
                intf_type = match.group(1).lower()
                intf_id = match.group(2)
                key, interface_type = self.normalize_interface_key(intf_type, intf_id)
                if key not in self.facts['interfaces']:
                    self.facts['interfaces'][key] = dict()
                if 'ipv6' not in self.facts['interfaces'][key]:
                    self.facts['interfaces'][key]['ipv6'] = list()
                continue

            if key is None:
                continue

            match = re.match(r'\W+ipv6 address (\S+)/(\S+)', line)
            match_ipv4 = re.match(r'\W+ip address (\S+) (\S+)', line)

            if match_ipv4:
                self.add_ip_address(match_ipv4.group(1), "ipv4", str(interface_type))
                ipv4 = {"address": match_ipv4.group(1), "subnet": match_ipv4.group(2)}
                if 'ipv4' not in self.facts['interfaces'][key]:
                    self.facts['interfaces'][key]['ipv4'] = ipv4
                elif isinstance(self.facts['interfaces'][key]['ipv4'], list):
                    if ipv4 not in self.facts['interfaces'][key]['ipv4']:
                        self.facts['interfaces'][key]['ipv4'].append(ipv4)
                elif self.facts['interfaces'][key]['ipv4'] != ipv4:
                    self.facts['interfaces'][key]['ipv4'] = [self.facts['interfaces'][key]['ipv4'], ipv4]

            if match:
                self.add_ip_address(match.group(1), "ipv6", str(interface_type))
                ipv6 = {"address": match.group(1), "subnet": match.group(2)}
                if ipv6 not in self.facts['interfaces'][key]['ipv6']:
                    self.facts['interfaces'][key]['ipv6'].append(ipv6)

    def normalize_interface_key(self, interface_type, interface_id):
        if interface_type == 'ethernet':
            return interface_id, interface_id
        if interface_type == 'management':
            return 'mgmt' + interface_id, 'management ' + interface_id
        if interface_type == 've':
            return 've' + interface_id, 've ' + interface_id
        if interface_type == 'lag':
            return interface_id, 'lag ' + interface_id
        return interface_type + interface_id, interface_type + ' ' + interface_id

    def add_ip_address(self, address, family, interface_type):
        if family == 'ipv4':
            if not self.facts['all_ipv4_addresses']:
                self.facts['all_ipv4_addresses'] = dict()
                self.facts['all_ipv4_addresses'][interface_type] = [address]
            elif self.facts['all_ipv4_addresses'].get(interface_type):
                self.facts['all_ipv4_addresses'][interface_type].append(address)
            else:
                self.facts['all_ipv4_addresses'][interface_type] = [address]
        else:
            if not self.facts['all_ipv6_addresses']:
                self.facts['all_ipv6_addresses'] = dict()
                self.facts['all_ipv6_addresses'][interface_type] = [address]
            elif self.facts['all_ipv6_addresses'].get(interface_type):
                self.facts['all_ipv6_addresses'][interface_type].append(address)
            else:
                self.facts['all_ipv6_addresses'][interface_type] = [address]

    def parse_neighbors(self, neighbors):
        facts = dict()
        for entry in neighbors.split('Local '):
            entry = entry.strip()
            if not entry:
                continue
            intf = self.parse_lldp_intf(entry)
            if not intf:
                continue
            if intf not in facts:
                facts[intf] = list()
            fact = dict()
            fact['Port ID'] = self.parse_lldp_portid(entry)
            fact['Port Description'] = self.parse_lldp_port_desc(entry)
            fact['System capabilities'] = self.parse_lldp_system_capabilities(entry)
            fact['System name'] = self.parse_lldp_system_name(entry)
            fact['System description'] = self.parse_lldp_system_desc(entry)
            fact['Neighbor'] = self.parse_lldp_neighbor(entry)

            facts[intf].append(fact)
        return facts

    def parse_interfaces(self, data):
        parsed = dict()
        key = ''
        for line in data.split('\n'):
            if len(line) == 0:
                continue
            elif line[0] == ' ':
                parsed[key] += '\n%s' % line
            else:
                match = re.match(r'\S+Ethernet(\S+)', line)
                if match:
                    key = match.group(1)
                    parsed[key] = line
        return parsed

    def parse_description(self, data):
        match = re.search(r'Port name is ([ \S]+)', data, re.M)
        if match:
            return match.group(1)

    def parse_macaddress(self, data):
        match = re.search(r'Hardware is \S+, address is (\S+)', data)
        if match:
            return match.group(1)

    def parse_ipv4(self, data):
        match = re.search(r'Internet address is (\S+)', data)
        if match:
            addr, masklen = match.group(1).split('/')
            return dict(address=addr, masklen=int(masklen))

    def parse_mtu(self, data):
        match = re.search(r'MTU (\d+)', data)
        if match:
            return int(match.group(1))

    def parse_bandwidth(self, data):
        match = re.search(r'Configured speed (\S+), actual (\S+)', data)
        if match:
            return match.group(1)

    def parse_duplex(self, data):
        match = re.search(r'configured duplex (\S+), actual (\S+)', data, re.M)
        if match:
            return match.group(2)

    def parse_mediatype(self, data):
        match = re.search(r'media type is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_type(self, data):
        match = re.search(r'Hardware is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lineprotocol(self, data):
        match = re.search(r'line protocol is (.+)$', data, re.M)
        if match:
            return match.group(1)

    def parse_operstatus(self, data):
        match = re.search(r'^(?:.+) is (.+),', data, re.M)
        if match:
            return match.group(1)

    def parse_lldp_intf(self, data):
        match = re.search(r'^port:\s*(.+)$', data, re.M | re.I)
        if match:
            return match.group(1).strip()

    def parse_lldp_system_name(self, data):
        match = re.search(r'System name\s*:\s*\"?(.*?)\"?$', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_lldp_portid(self, data):
        match = re.search(r'Port ID.*: *(.+)$', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_lldp_port_desc(self, data):
        match = re.search(r'Port description\s*:\s*\"?(.*?)\"?$', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_lldp_system_capabilities(self, data):
        match = re.search(r'System capabilities\s*:\s*\"?(.*?)\"?$', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_lldp_system_desc(self, data):
        match = re.search(r'System description *: *"(.+)"$', data, re.M | re.I)
        if match:
            return match.group(1)

    def parse_lldp_neighbor(self, data):
        match = re.search(r'Neighbor *: *([^,]+)', data, re.M | re.I)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

warnings = list()


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset')

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
