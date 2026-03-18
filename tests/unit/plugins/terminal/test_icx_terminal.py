from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.commscope.icx.tests.unit.compat import unittest
from ansible_collections.commscope.icx.plugins.terminal.icx import TerminalModule


class TestICXTerminal(unittest.TestCase):

    def test_terminal_prompt_regex_ignores_invalid_input_arrow(self):
        response = (
            b"totally-invalid-icx-command\r\n"
            b"Invalid input ->totally-invalid-icx-command\r\n"
            b"Type ? for a list\r\n"
        )

        self.assertIsNone(TerminalModule.terminal_stdout_re[0].search(response))

    def test_terminal_prompt_regex_matches_real_prompt_after_error(self):
        response = (
            b"totally-invalid-icx-command\r\n"
            b"Invalid input ->totally-invalid-icx-command\r\n"
            b"Type ? for a list\r\n"
            b"Node doesn't exist\r\n"
            b"SSH@ICX7150-1(config)#"
        )

        match = TerminalModule.terminal_stdout_re[0].search(response)
        self.assertIsNotNone(match)
        self.assertEqual(match.group().strip(), b"SSH@ICX7150-1(config)#")
