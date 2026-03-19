# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.commscope.icx.tests.unit.compat.mock import patch
from ansible_collections.commscope.icx.plugins.modules import icx_vlan
from ansible_collections.commscope.icx.tests.unit.plugins.modules.utils import set_module_args
from .icx_module import TestICXModule


class TestICXVlanModule(TestICXModule):

    module = icx_vlan

    def setUp(self):
        super(TestICXVlanModule, self).setUp()
        self.mock_exec_command = patch('ansible_collections.commscope.icx.plugins.modules.icx_vlan.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_vlan.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_vlan.get_config')
        self.get_config = self.mock_get_config.start()

        self.set_running_config()

    def tearDown(self):
        super(TestICXVlanModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None):
        self.load_config.return_value = None

    def test_icx_vlan_missing_target_skips_extra_lookups(self):
        def fake_exec(module, command):
            if command == 'skip':
                return (0, '', None)
            if command == 'show vlan brief':
                return (0, '\n'.join([
                    'System-max vlan Params: Max(4095) Default(64) Current(64)',
                    'VLANs Configured :1 3 6 10 21',
                ]), None)
            raise AssertionError('unexpected command: %s' % command)

        self.exec_command.side_effect = fake_exec

        set_module_args(dict(name='VLAN-WYSI', vlan_id=727, check_running_config=True))
        result = self.execute_module(changed=True, sort=False)

        self.assertEqual(result['commands'], ['vlan 727', 'vlan 727 name VLAN-WYSI', 'exit'])
        self.get_config.assert_not_called()
        self.assertEqual(
            [call[0][1] for call in self.exec_command.call_args_list],
            ['skip', 'show vlan brief']
        )

    def test_icx_vlan_existing_target_uses_targeted_queries(self):
        def fake_exec(module, command):
            if command == 'skip':
                return (0, '', None)
            if command == 'show vlan brief':
                return (0, '\n'.join([
                    'System-max vlan Params: Max(4095) Default(64) Current(64)',
                    'VLANs Configured :1 3 6 10 21',
                ]), None)
            if command == 'show run vlan 3':
                return (0, '\n'.join([
                    'vlan 3 name vlan by port',
                    ' tagged ethe 1/1/31 ethe 1/1/9 to 1/1/11 lag 13',
                    ' untagged ethe 1/1/27 ethe 1/1/20 to 1/1/22 lag 11 to 12',
                    ' spanning-tree',
                    '!',
                ]), None)
            if command == 'show vlan 3':
                return (0, 'PORT-VLAN 3, Name vlan, Priority level0, Spanning tree On', None)
            raise AssertionError('unexpected command: %s' % command)

        self.exec_command.side_effect = fake_exec

        set_module_args(dict(vlan_id=3, check_running_config=True))
        self.execute_module(changed=False)

        self.get_config.assert_not_called()
        self.assertEqual(
            [call[0][1] for call in self.exec_command.call_args_list],
            ['skip', 'show vlan brief', 'show run vlan 3', 'show vlan 3']
        )

    def test_icx_vlan_existing_target_renames_vlan(self):
        def fake_exec(module, command):
            if command == 'skip':
                return (0, '', None)
            if command == 'show vlan brief':
                return (0, '\n'.join([
                    'System-max vlan Params: Max(4095) Default(64) Current(64)',
                    'VLANs Configured :1 727',
                ]), None)
            if command == 'show run vlan 727':
                return (0, 'vlan 727 name VLAN-WYSI by port\n!\n!\n', None)
            if command == 'show vlan 727':
                return (0, 'PORT-VLAN 727, Name VLAN-WYSI, Priority level0, Off', None)
            raise AssertionError('unexpected command: %s' % command)

        self.exec_command.side_effect = fake_exec

        set_module_args(dict(name='VLAN-WYSI-1', vlan_id=727, check_running_config=True))
        result = self.execute_module(changed=True, sort=False)

        self.assertEqual(result['commands'], ['vlan 727 name VLAN-WYSI-1'])
