#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: icx_ntp
author: "Ruckus Wireless (@Commscope)"
short_description: Manage NTP server configuration on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of NTP servers on
    Ruckus ICX 7000 series switches.
  - The module manages the server addresses configured under the
    C(ntp) submode.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  servers:
    description:
      - Ordered list of NTP server addresses or hostnames.
      - When I(state=present), the configured NTP server list will be reconciled to match this list.
      - When I(state=absent), the listed servers will be removed.
    type: list
    elements: str
    required: true
  state:
    description:
      - State of the NTP server configuration.
    type: str
    default: present
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:False), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: no
'''

EXAMPLES = """
- name: Configure NTP servers
  community.network.icx_ntp:
    servers:
      - 10.126.11.12
      - 10.138.11.12

- name: Remove one NTP server
  community.network.icx_ntp:
    servers:
      - 10.126.11.12
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ntp
    - server 10.126.11.12
"""


import re

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.commscope.icx.plugins.module_utils.network.icx.icx import get_config, load_config


def diff_list(want, have):
    adds = [w for w in want if w not in have]
    removes = [h for h in have if h not in want]
    return adds, removes


def parse_ntp_servers(config):
    servers = []
    in_ntp = False

    for line in config.splitlines():
        stripped = line.strip()
        if stripped == 'ntp':
            in_ntp = True
            continue

        if not in_ntp:
            continue

        if stripped == '!':
            break

        if line and not line[0].isspace():
            break

        match = re.match(r'^\s+server\s+(\S+)', line)
        if match:
            servers.append(match.group(1))

    return servers


def map_config_to_obj(module):
    compare = module.params['check_running_config']
    config = get_config(module, None, compare=compare)
    return {'servers': parse_ntp_servers(config)}


def map_params_to_obj(module):
    return {
        'servers': module.params['servers'] or [],
        'state': module.params['state'],
    }


def map_obj_to_commands(want, have, module):
    state = module.params['state']
    commands = []

    if state == 'present':
        adds, removes = diff_list(want['servers'], have['servers'])
        if adds or removes:
            commands.append('ntp')
            for server in removes:
                commands.append('no server %s' % server)
            for server in adds:
                commands.append('server %s' % server)

    elif state == 'absent':
        if module.params['check_running_config']:
            removes = [server for server in want['servers'] if server in have['servers']]
        else:
            removes = want['servers']

        if removes:
            commands.append('ntp')
            for server in removes:
                commands.append('no server %s' % server)

    return commands


def main():
    argument_spec = dict(
        servers=dict(type='list', elements='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        check_running_config=dict(default=False, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
