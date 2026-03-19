#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: icx_l3_interface
author: "Ruckus Wireless (@Commscope)"
short_description: Manage Layer-3 interfaces on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of Layer-3 interfaces
    on ICX network devices.
notes:
  - Tested against ICX 8.0.95
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  name:
    description:
      - Name of the Layer-3 interface to be configured eg. GigabitEthernet0/2, ve 10, ethernet 1/1/1
    type: str
  ipv4:
    description:
      - IPv4 address to be set for the Layer-3 interface mentioned in I(name) option.
        The address format is <ipv4 address>/<mask>, the mask is number
        in range 0-32 eg. 192.168.0.1/24
    type: str
  ipv6:
    description:
      - IPv6 address to be set for the Layer-3 interface mentioned in I(name) option.
        The address format is <ipv6 address>/<mask>, the mask is number
        in range 0-128 eg. fd5d:12c9:2201:1::1/64.
    type: str
  mode:
    description:
      - Specifies if ipv4 address should be dynamic/advertise to ospf/not advertise to ospf.
        This should be specified only if ipv4 address is configured and if it is not secondary IP address.
    choices: ['dynamic', 'ospf-ignore', 'ospf-passive']
    type: str
  replace:
    description:
      - Replaces the configured primary IP address on the interface.
    type: bool
  secondary:
    description:
      - Specifies that the configured address is a secondary IP address.
        If this keyword is omitted, the configured address is the primary IP address.
    type: bool
  helper_addresses:
    description:
      - List of DHCP relay helper addresses to configure on the interface.
      - When I(state=present), the configured helper addresses are reconciled to match this list.
      - When I(state=absent), the listed helper addresses are removed.
      - Setting this to an empty list with I(state=present) removes all helper addresses from the interface.
    type: list
    elements: str
  aggregate:
    description:
      - List of Layer-3 interfaces definitions. Each of the entry in aggregate list should
        define name of interface C(name) and an optional C(ipv4), C(ipv6), or C(helper_addresses).
    type: list
    suboptions:
      name:
        description:
          - Name of the Layer-3 interface to be configured eg. GigabitEthernet0/2, ve 10, ethernet 1/1/1
        type: str
      ipv4:
        description:
          - IPv4 address to be set for the Layer-3 interface mentioned in I(name) option.
            The address format is <ipv4 address>/<mask>, the mask is number
            in range 0-32 eg. 192.168.0.1/24
        type: str
      ipv6:
        description:
          - IPv6 address to be set for the Layer-3 interface mentioned in I(name) option.
            The address format is <ipv6 address>/<mask>, the mask is number
            in range 0-128 eg. fd5d:12c9:2201:1::1/64.
        type: str
      mode:
        description:
          - Specifies if ipv4 address should be dynamic/advertise to ospf/not advertise to ospf.
            This should be specified only if ipv4 address is configured and if it is not secondary IP address.
        choices: ['dynamic', 'ospf-ignore', 'ospf-passive']
        type: str
      replace:
        description:
          - Replaces the configured primary IP address on the interface.
        type: bool
      secondary:
        description:
          - Specifies that the configured address is a secondary IP address.
            If this keyword is omitted, the configured address is the primary IP address.
        type: bool
      helper_addresses:
        description:
          - List of DHCP relay helper addresses to configure on the interface.
        type: list
        elements: str
      state:
        description:
          - State of the Layer-3 interface configuration. It indicates if the configuration should
            be present or absent on remote device.
        choices: ['present', 'absent']
        type: str
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
           Module will use environment variable value(default:False), unless it is overridden, by specifying it as module parameter.
        type: bool
  state:
    description:
      - State of the Layer-3 interface configuration. It indicates if the configuration should
        be present or absent on remote device.
    default: present
    choices: ['present', 'absent']
    type: str
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:False), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: no
'''

EXAMPLES = """
- name: Remove ethernet 1/1/1 IPv4 and IPv6 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    ipv6: "fd5d:12c9:2201:1::1/64"
    state: absent
- name: Replace ethernet 1/1/1 primary IPv4 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    replace: yes
    state: absent
- name: Replace ethernet 1/1/1 dynamic IPv4 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    mode: dynamic
    state: absent
- name: Set ethernet 1/1/1 secondary IPv4 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
    secondary: yes
    state: absent
- name: Set ethernet 1/1/1 IPv4 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv4: 192.168.0.1/24
- name: Set ethernet 1/1/1 IPv6 address
  community.network.icx_l3_interface:
    name: ethernet 1/1/1
    ipv6: "fd5d:12c9:2201:1::1/64"
- name: Configure DHCP relay helper addresses on a VE
  community.network.icx_l3_interface:
    name: ve 727
    helper_addresses:
      - 192.168.50.11
      - 192.168.50.12
- name: Set IP addresses on aggregate
  community.network.icx_l3_interface:
    aggregate:
      - { name: GigabitEthernet0/3, ipv4: 192.168.2.10/24 }
      - { name: GigabitEthernet0/3, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }
- name: Remove IP addresses on aggregate
  community.network.icx_l3_interface:
    aggregate:
      - { name: GigabitEthernet0/3, ipv4: 192.168.2.10/24 }
      - { name: GigabitEthernet0/3, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }
    state: absent
- name: Set the ipv4 and ipv6 of a virtual ethernet(ve)
  community.network.icx_l3_interface:
    name: ve 100
    ipv4: 192.168.0.1
    ipv6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface ethernet 1/1/1
    - ip address 192.168.0.1 255.255.255.0
    - ipv6 address fd5d:12c9:2201:1::1/64
"""


import re
from copy import deepcopy
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import exec_command
from ansible_collections.commscope.icx.plugins.module_utils.network.icx.icx import get_config, load_config
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import remove_default_spec
try:
    from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import is_netmask, is_masklen, to_netmask, to_masklen
except ImportError:
    # ansible.netcommon >= 8 removed these helpers; ansible-core still ships them.
    from ansible.module_utils.common.network import is_netmask, is_masklen, to_netmask, to_masklen


def validate_ipv4(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv4 address>/<mask>, got invalid format %s' % value)
        else:
            if not is_masklen(address[1]):
                module.fail_json(msg='invalid value for mask: %s, mask should be in range 0-32' % address[1])


def validate_ipv6(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv6 address>/<mask>, got invalid format %s' % value)
        else:
            if not 0 <= int(address[1]) <= 128:
                module.fail_json(msg='invalid value for mask: %s, mask should be in range 0-128' % address[1])


def validate_helper_addresses(value, module):
    if value is None:
        return

    duplicates = set()
    seen = set()
    for address in value:
        if address in seen:
            duplicates.add(address)
        seen.add(address)

    if duplicates:
        module.fail_json(msg='duplicate helper_addresses are not allowed: %s' % ', '.join(sorted(duplicates)))


def validate_param_values(module, obj, param=None):
    if param is None:
        param = module.params
    for key in obj:
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            validate_param_values(module, item, item)
            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'],
            'ipv4': module.params['ipv4'],
            'ipv6': module.params['ipv6'],
            'helper_addresses': module.params['helper_addresses'],
            'state': module.params['state'],
            'replace': module.params['replace'],
            'mode': module.params['mode'],
            'secondary': module.params['secondary'],
        })

        validate_param_values(module, obj[0], obj[0])

    return obj


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)

    values = []
    matches = re.finditer(r'%s (.+)$' % arg, cfg, re.M)
    for match in matches:
        match_str = match.group(1).strip()
        if arg == 'ipv6 address':
            values.append(match_str)
        else:
            values = match_str
            break

    return values or None


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def parse_helper_addresses(configobj, name):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)

    helpers = []
    matches = re.finditer(r'^ip helper-address (\d+) (\S+)$', cfg, re.M)
    for match in matches:
        helpers.append({
            'index': int(match.group(1)),
            'address': match.group(2),
        })

    return sorted(helpers, key=lambda item: item['index'])


def diff_helper_addresses(want, have):
    adds = [address for address in want if address not in [item['address'] for item in have]]
    removes = [item for item in have if item['address'] not in want]
    return adds, removes


def get_next_helper_index(used_indices):
    index = 1
    while index in used_indices:
        index += 1
    used_indices.add(index)
    return index


def get_target_interface_names(want):
    targets = []
    seen = set()

    for item in want:
        name = item['name']
        if name not in seen:
            seen.add(name)
            targets.append(name)

    return targets


def iter_interface_blocks(config):
    current_name = None
    current_lines = []

    for line in config.splitlines():
        if line.startswith('interface '):
            if current_name is not None:
                yield current_name, '\n'.join(current_lines)
            current_name = line[len('interface '):].strip()
            current_lines = [line]
            continue

        if current_name is None:
            continue

        current_lines.append(line)
        if line.strip() == '!':
            yield current_name, '\n'.join(current_lines)
            current_name = None
            current_lines = []

    if current_name is not None and current_lines:
        yield current_name, '\n'.join(current_lines)


def map_config_to_obj(module, want=None):
    compare = module.params['check_running_config']
    if not compare:
        return list()

    want = want or map_params_to_obj(module)
    targets = get_target_interface_names(want)
    flags = ['| begin interface']
    if len(targets) == 1:
        flags = ['| begin interface %s' % targets[0]]

    config = get_config(module, flags=flags, compare=compare)
    blocks = list(iter_interface_blocks(config))
    if targets:
        target_set = set(targets)
        blocks = [block for block in blocks if block[0] in target_set]

    if not blocks:
        return list()

    configobj = NetworkConfig(indent=1, contents='\n'.join(block for _, block in blocks))
    instances = list()

    for item, _block in blocks:
        ipv4 = parse_config_argument(configobj, item, 'ip address')
        if ipv4:
            address = ipv4.strip().split(' ')
            if len(address) == 2 and is_netmask(address[1]):
                ipv4 = '{0}/{1}'.format(address[0], to_text(to_masklen(address[1])))
        helper_entries = parse_helper_addresses(configobj, item)
        obj = {
            'name': item,
            'ipv4': ipv4,
            'ipv6': parse_config_argument(configobj, item, 'ipv6 address'),
            'helper_addresses': [item['address'] for item in helper_entries],
            'helper_address_slots': helper_entries,
            'state': 'present'
        }
        instances.append(obj)

    return instances


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    for w in want:
        name = w['name']
        ipv4 = w['ipv4']
        ipv6 = w['ipv6']
        helper_addresses = w.get('helper_addresses')
        state = w['state']
        replace = bool(w.get('replace'))
        if w['mode'] is not None:
            mode = ' ' + w['mode']
        else:
            mode = ''
        secondary = bool(w.get('secondary'))

        interface = 'interface ' + name
        commands.append(interface)

        obj_in_have = search_obj_in_list(name, have)
        have_helper_slots = obj_in_have.get('helper_address_slots', []) if obj_in_have else []
        if state == 'absent' and have == []:
            if ipv4:
                address = ipv4.split('/')
                if len(address) == 2:
                    ipv4 = '{addr} {mask}'.format(addr=address[0], mask=to_netmask(address[1]))
                commands.append('no ip address {ip}'.format(ip=ipv4))
            if ipv6:
                commands.append('no ipv6 address {ip}'.format(ip=ipv6))
            if helper_addresses and not module.params['check_running_config']:
                module.fail_json(msg='check_running_config=true is required to remove helper_addresses')

        elif state == 'absent' and obj_in_have:
            if obj_in_have['ipv4']:
                if ipv4:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{addr} {mask}'.format(addr=address[0], mask=to_netmask(address[1]))
                    commands.append('no ip address {ip}'.format(ip=ipv4))
            if obj_in_have['ipv6']:
                if ipv6:
                    commands.append('no ipv6 address {ip}'.format(ip=ipv6))
            if helper_addresses:
                for helper in have_helper_slots:
                    if helper['address'] in helper_addresses:
                        commands.append('no ip helper-address {index} {address}'.format(index=helper['index'], address=helper['address']))

        elif state == 'present':
            if ipv4:
                if obj_in_have is None or obj_in_have.get('ipv4') is None or ipv4 != obj_in_have['ipv4']:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{0} {1}'.format(address[0], to_netmask(address[1]))
                    commands.append('ip address %s%s%s%s' % (format(ipv4), mode, ' replace' if (replace) else '', ' secondary' if (secondary) else ''))

            if ipv6:
                if obj_in_have is None or obj_in_have.get('ipv6') is None or ipv6.lower() not in [addr.lower() for addr in obj_in_have['ipv6']]:
                    commands.append('ipv6 address {ip}'.format(ip=ipv6))

            if helper_addresses is not None:
                adds, removes = diff_helper_addresses(helper_addresses, have_helper_slots)
                used_indices = set(item['index'] for item in have_helper_slots)

                for helper in removes:
                    commands.append('no ip helper-address {index} {address}'.format(index=helper['index'], address=helper['address']))
                    used_indices.discard(helper['index'])

                for helper_address in adds:
                    helper_index = get_next_helper_index(used_indices)
                    commands.append('ip helper-address {index} {address}'.format(index=helper_index, address=helper_address))

        if commands[-1] == interface:
            commands.pop(-1)
        else:
            commands.append("exit")

    return commands


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        helper_addresses=dict(type='list', elements='str'),
        replace=dict(type='bool'),
        mode=dict(choices=['dynamic', 'ospf-ignore', 'ospf-passive']),
        secondary=dict(type='bool'),
        check_running_config=dict(default=False, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG'])),
        state=dict(default='present',
                   choices=['present', 'absent']),
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec)
    )

    argument_spec.update(element_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate'], ['secondary', 'replace'], ['secondary', 'mode']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    want = map_params_to_obj(module)
    have = map_config_to_obj(module, want)
    commands = map_obj_to_commands((want, have), module)

    if commands:
        if not module.check_mode:
            resp = load_config(module, commands)
            warnings.extend((out for out in resp if out))

        result['changed'] = True

    if warnings:
        result['warnings'] = warnings

    result['commands'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()
