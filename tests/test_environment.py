import unittest

from agent_welcome.environment import _architecture


class EnvironmentTests(unittest.TestCase):
    def test_32_bit_arm_kernel_name_is_not_promoted_to_aarch64(self):
        self.assertEqual(_architecture('armv8l'), 'armv8l')
        self.assertEqual(_architecture('aarch64'), 'aarch64')
        self.assertEqual(_architecture('arm64'), 'aarch64')


if __name__ == '__main__':
    unittest.main()
