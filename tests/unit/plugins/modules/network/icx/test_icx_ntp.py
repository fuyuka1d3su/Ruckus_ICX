# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.commscope.icx.tests.unit.compat.mock import patch
from ansible_collections.commscope.icx.plugins.modules import icx_ntp
from ansible_collections.commscope.icx.tests.unit.plugins.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXNtpModule(TestICXModule):

    module = icx_ntp

    def setUp(self):
        super(TestICXNtpModule, self).setUp()

        self.mock_get_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_ntp.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible_collections.commscope.icx.plugins.modules.icx_ntp.load_config')
        self.load_config = self.mock_load_config.start()

        self.set_running_config()

    def tearDown(self):
        super(TestICXNtpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        def load_file(*args, **kwargs):
            module = args[0]
            if module.params['check_running_config'] is True:
                return load_fixture('icx_ntp_config.cfg').strip()
            return ''

        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_parse_ntp_servers(self):
        config = load_fixture('icx_ntp_config.cfg')
        self.assertEqual(
            icx_ntp.parse_ntp_servers(config),
            ['192.168.100.10', '192.168.100.11']
        )

    def test_icx_ntp_add_servers_without_compare(self):
        set_module_args(dict(servers=['192.168.100.10', '192.168.100.11'], check_running_config=False))
        result = self.execute_module(changed=True, sort=False)
        self.assertEqual(result['commands'], ['ntp', 'server 192.168.100.10', 'server 192.168.100.11'])
        self.get_config.assert_not_called()

    def test_icx_ntp_reconcile_servers(self):
        set_module_args(dict(
            servers=['192.168.100.10', '192.168.100.12'],
            check_running_config=True
        ))
        result = self.execute_module(changed=True, sort=False)
        self.assertEqual(result['commands'], ['ntp', 'no server 192.168.100.11', 'server 192.168.100.12'])
        self.assertEqual(self.get_config.call_args[1]['flags'], ['| begin ntp'])

    def test_icx_ntp_remove_servers(self):
        set_module_args(dict(
            servers=['192.168.100.11'],
            state='absent',
            check_running_config=True
        ))
        result = self.execute_module(changed=True, sort=False)
        self.assertEqual(result['commands'], ['ntp', 'no server 192.168.100.11'])

    def test_icx_ntp_no_change(self):
        set_module_args(dict(
            servers=['192.168.100.10', '192.168.100.11'],
            check_running_config=True
        ))
        self.execute_module(changed=False)
