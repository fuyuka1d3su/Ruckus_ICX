# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible_collections.commscope.icx.tests.unit.compat.mock import patch
from ansible_collections.commscope.icx.plugins.modules import icx_system
from ansible_collections.commscope.icx.tests.unit.plugins.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXSystemModule(TestICXModule):

    module = icx_system

    def setUp(self):
        super(TestICXSystemModule, self).setUp()

        self.mock_get_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_system.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_system.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_exec_command = patch('ansible_collections.commscope.icx.plugins.modules.icx_system.exec_command')
        self.exec_command = self.mock_exec_command.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXSystemModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is True:
                    return load_fixture('icx_system.txt').strip()
                else:
                    return ''

        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_icx_system_set_config(self):
        set_module_args(dict(hostname='ruckus', name_servers=['172.16.10.2', '11.22.22.4'], domain_search=['ansible.com', 'redhat.com']))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'hostname ruckus',
                'ip dns domain-list ansible.com',
                'ip dns domain-list redhat.com',
                'ip dns server-address 11.22.22.4',
                'ip dns server-address 172.16.10.2',
                'no ip dns domain-list ansib.eg.com',
                'no ip dns domain-list red.com',
                'no ip dns domain-list test1.com',
                'no ip dns server-address 10.22.22.64',
                'no ip dns server-address 172.22.22.64'
            ]
            self.execute_module(changed=True, commands=commands)

        else:
            commands = [
                'hostname ruckus',
                'ip dns domain-list ansible.com',
                'ip dns domain-list redhat.com',
                'ip dns server-address 11.22.22.4',
                'ip dns server-address 172.16.10.2'
            ]
            self.execute_module(changed=True, commands=commands)

    def test_icx_system_remove_config(self):
        set_module_args(dict(name_servers=['10.22.22.64', '11.22.22.4'], domain_search=['ansib.eg.com', 'redhat.com'], state='absent'))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'no ip dns domain-list ansib.eg.com',
                'no ip dns server-address 10.22.22.64',
            ]
            self.execute_module(changed=True, commands=commands)

        else:
            commands = [
                'no ip dns domain-list ansib.eg.com',
                'no ip dns domain-list redhat.com',
                'no ip dns server-address 10.22.22.64',
                'no ip dns server-address 11.22.22.4'
            ]
            self.execute_module(changed=True, commands=commands)

    def test_icx_system_remove_config_compare(self):
        set_module_args(
            dict(
                name_servers=[
                    '10.22.22.64',
                    '11.22.22.4'],
                domain_search=[
                    'ansib.eg.com',
                    'redhat.com'],
                state='absent',
                check_running_config=True))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                commands = [
                    'no ip dns domain-list ansib.eg.com',
                    'no ip dns server-address 10.22.22.64',
                ]
                self.execute_module(changed=True, commands=commands)
            else:
                commands = [
                    'no ip dns domain-list ansib.eg.com',
                    'no ip dns server-address 10.22.22.64',
                ]
                self.execute_module(changed=True, commands=commands)

    def test_icx_aaa_servers_radius_set(self):
        radius = [
            dict(
                type='radius',
                hostname='2001:db8::1',
                auth_port_type='auth-port',
                auth_port_num='1821',
                acct_port_num='1321',
                acct_type='accounting-only',
                auth_key='radius',
                auth_key_type=[
                    'mac-auth']),
            dict(
                type='radius',
                hostname='172.16.10.24',
                auth_port_type='auth-port',
                auth_port_num='2001',
                acct_port_num='5000',
                acct_type='authentication-only',
                auth_key='radius-server'),
            dict(
                type='tacacs',
                hostname='ansible.com')]
        set_module_args(dict(hostname='ruckus', aaa_servers=radius))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                'hostname ruckus',
                'no radius-server host 172.16.20.14',
                'no tacacs-server host 182.16.10.20',
                'radius-server host 172.16.10.24 auth-port 2001 acct-port 5000 authentication-only key radius-server',
                'radius-server host ipv6 2001:db8::1 auth-port 1821 acct-port 1321 accounting-only key radius mac-auth',
                'tacacs-server host ansible.com'
            ]
            self.execute_module(changed=True, commands=commands)
        else:
            commands = [
                'hostname ruckus',
                'radius-server host 172.16.10.24 auth-port 2001 acct-port 5000 authentication-only key radius-server',
                'radius-server host ipv6 2001:db8::1 auth-port 1821 acct-port 1321 accounting-only key radius mac-auth',
                'tacacs-server host ansible.com'
            ]
            self.execute_module(changed=True, commands=commands)

    def test_parse_aaa_servers_ignores_global_radius_settings(self):
        config = """
radius-server dead-time 1
radius-server accounting interim-updates
radius-server accounting interim-interval 5
radius-server host 172.16.1.10 auth-port 1812 acct-port 1813 default key XXX dot1x mac-auth web-auth
"""
        self.assertEqual(
            icx_system.parse_aaa_servers(config),
            [dict(
                type='radius',
                hostname='172.16.1.10',
                auth_port_type='auth-port',
                auth_port_num='1812',
                acct_port_num='1813',
                acct_type='default',
                auth_key=None,
                auth_key_type={'dot1x', 'mac-auth', 'web-auth'}
            )]
        )

    def test_icx_system_absent_with_global_radius_settings(self):
        set_module_args(dict(
            aaa_servers=[dict(
                type='radius',
                hostname='172.16.1.10',
                auth_port_type='auth-port',
                auth_port_num='1812',
                acct_port_num='1813',
                acct_type='default',
                auth_key='doesntmatter',
                auth_key_type=['dot1x', 'mac-auth', 'web-auth']
            )],
            state='absent',
            check_running_config=True
        ))
        self.get_config.return_value = """
radius-server dead-time 1
radius-server accounting interim-updates
radius-server accounting interim-interval 5
radius-server host 172.16.1.10 auth-port 1812 acct-port 1813 default key XXX dot1x mac-auth web-auth
"""
        self.load_config.return_value = None

        result = self.changed(changed=True)
        self.assertEqual(result['commands'], ['no radius-server host 172.16.1.10'])
