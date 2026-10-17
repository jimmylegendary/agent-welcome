import os
import unittest
from unittest.mock import patch

from agent_welcome import environment
from agent_welcome.environment import _architecture


class EnvironmentTests(unittest.TestCase):
    def test_32_bit_arm_kernel_name_is_not_promoted_to_aarch64(self):
        self.assertEqual(_architecture('armv8l'), 'armv8l')
        self.assertEqual(_architecture('aarch64'), 'aarch64')
        self.assertEqual(_architecture('arm64'), 'aarch64')

    def test_android_system_and_api_observations_are_native_linux_kernel(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            environment.platform, 'machine', return_value='aarch64',
        ), patch.object(environment.platform, 'libc_ver', return_value=('bionic', '')):
            with patch.object(environment.platform, 'system', return_value='Android'):
                direct_android = environment.observe()
            with patch.object(environment.platform, 'system', return_value='Linux'), patch.object(
                environment.sys, 'getandroidapilevel', return_value=34, create=True,
            ):
                android_api = environment.observe()
        for observation in (direct_android, android_api):
            with self.subTest(observation=observation['provenance']['host_os_method']):
                self.assertEqual(observation['kernel_os'], 'linux')
                self.assertEqual(observation['host_os'], 'android')
                self.assertEqual(observation['runtime_kind'], 'native')


if __name__ == '__main__':
    unittest.main()
