import json
import unittest
from pathlib import Path

from agent_welcome.catalog import (
    CatalogError,
    evaluate_condition,
    evaluate_route,
    load_catalog,
    load_recipe,
    validate_catalog,
    validate_recipe,
)


ROOT = Path(__file__).resolve().parents[1]


class ConditionTests(unittest.TestCase):
    def test_version_comparison_uses_numeric_components(self):
        observations = {'libc': {'version': '2.9'}}
        self.assertEqual(
            evaluate_condition(
                {'op': 'version_gte', 'fact': 'libc.version', 'value': '2.35'},
                observations,
            )['status'],
            'fail',
        )
        observations['libc']['version'] = '2.35'
        self.assertEqual(
            evaluate_condition(
                {'op': 'version_gte', 'fact': 'libc.version', 'value': '2.35.0'},
                observations,
            )['status'],
            'pass',
        )

    def test_unknown_fact_is_not_a_pass(self):
        result = evaluate_condition(
            {'op': 'eq', 'fact': 'capabilities.user_namespace', 'value': True},
            {},
        )
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['missing_facts'], ['capabilities.user_namespace'])

    def test_nested_all_any_eq_and_in_conditions(self):
        condition = {
            'op': 'all',
            'conditions': [
                {'op': 'eq', 'fact': 'os', 'value': 'linux'},
                {
                    'op': 'any',
                    'conditions': [
                        {'op': 'in', 'fact': 'architecture', 'values': ['aarch64', 'x86_64']},
                        {'op': 'eq', 'fact': 'architecture', 'value': 'armv7'},
                    ],
                },
            ],
        }
        self.assertEqual(
            evaluate_condition(condition, {'os': 'linux', 'architecture': 'aarch64'})['status'],
            'pass',
        )
        self.assertEqual(
            evaluate_condition(condition, {'os': 'linux', 'architecture': 'riscv64'})['status'],
            'fail',
        )

    def test_unknown_operator_and_malformed_version_are_validation_errors(self):
        with self.assertRaises(CatalogError):
            evaluate_condition({'op': 'regex', 'fact': 'os', 'value': 'linux'}, {'os': 'linux'})
        with self.assertRaises(CatalogError):
            evaluate_condition({'op': [], 'fact': 'os', 'value': 'linux'}, {'os': 'linux'})
        with self.assertRaises(CatalogError):
            evaluate_condition(
                {'op': 'version_gte', 'fact': 'libc.version', 'value': '2.x'},
                {'libc': {'version': '2.35'}},
            )
        with self.assertRaises(CatalogError):
            evaluate_condition(
                {'op': 'version_gte', 'fact': 'libc.version', 'value': '2.35'},
                {'libc': {'version': '2.x'}},
            )
        with self.assertRaises(CatalogError):
            evaluate_condition({'op': 'eq', 'fact': 'os', 'value': 'linux'}, {'os': []})

    def test_in_operator_does_not_coerce_bool_to_integer_equality(self):
        result = evaluate_condition(
            {'op': 'in', 'fact': 'enabled', 'values': [False, 1]},
            {'enabled': True},
        )
        self.assertEqual(result['status'], 'fail')

    def test_known_observation_fields_reject_wrong_types_but_null_remains_unknown(self):
        condition = {'op': 'eq', 'fact': 'kernel_os', 'value': 'linux'}
        invalid = [
            {'kernel_os': 'linux', 'host_os': False},
            {'kernel_os': 'linux', 'runtime_kind': 123},
            {'kernel_os': 'linux', 'capabilities': 'bad'},
        ]
        for observations in invalid:
            with self.subTest(observations=observations), self.assertRaises(CatalogError):
                evaluate_condition(condition, observations)
        result = evaluate_condition(
            {'op': 'eq', 'fact': 'host_os', 'value': 'android'},
            {'kernel_os': 'linux', 'host_os': None, 'runtime_kind': None,
             'capabilities': None},
        )
        self.assertEqual(result['status'], 'unknown')


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = load_catalog(ROOT / 'kg' / 'graph.json')

    def test_graph_is_schema_02_with_bounded_relations_and_resolved_bindings(self):
        self.assertEqual(self.graph['schema_version'], '0.2')
        self.assertFalse(self.graph['runtime_tested'])
        self.assertFalse(self.graph['direct_reproduction'])
        validate_catalog(self.graph)
        self.assertEqual(len(self.graph['recovery_playbooks']), 5)
        for playbook in self.graph['recovery_playbooks']:
            for field in ('applicability', 'agent_id', 'symptom_id', 'diagnostic_ids',
                          'route_ids', 'required_check_ids'):
                self.assertIn(field, playbook)
            self.assertTrue(playbook['applicability'])

    def test_published_json_schemas_are_well_formed(self):
        for schema_path in (ROOT / 'schemas').glob('*.json'):
            with self.subTest(schema=schema_path.name):
                self.assertIsInstance(json.loads(schema_path.read_text()), dict)

    def test_claude_agent_is_connected_to_a_candidate_route(self):
        nodes = {n['id']: n for n in self.graph['nodes']}
        route_ids = {
            link['target'] for link in self.graph['links']
            if link['source'] == 'agent_claude' and link['relation'] == 'candidate_for'
        }
        self.assertTrue(route_ids)
        self.assertTrue(any(nodes[r].get('type') in {
            'community_route', 'preservation_route', 'modified_artifact_route',
            'recovery_candidate',
        } for r in route_ids))

    def test_codex_proot_route_cannot_pass_without_sandbox_check(self):
        result = evaluate_route(
            self.graph,
            'route_codux_community',
            {'kernel_os': 'linux', 'host_os': 'android',
             'architecture': 'aarch64', 'runtime_kind': 'proot'},
            {},
        )
        self.assertNotEqual(result['status'], 'pass')
        self.assertIn('check_sandbox', result['missing_checks'])

    def test_every_codex_route_requires_artifact_readonly_sandbox_and_profile_checks(self):
        check_results = {
            'check_agent_version': True,
            'check_sandbox': True,
            'check_account_permission': True,
            'check_login_and_readonly_task': True,
            'check_permission_profile': True,
        }
        codux = evaluate_route(
            self.graph,
            'route_codux_community',
            {'kernel_os': 'linux', 'host_os': 'android',
             'architecture': 'aarch64', 'runtime_kind': 'proot'},
            check_results,
        )
        self.assertNotEqual(codux['status'], 'pass')
        for check_id in (
            'check_artifact_integrity',
            'check_agent_runtime_compatibility',
            'check_permission_profile',
        ):
            self.assertIn(check_id, codux['missing_checks'])
        self.assertIn('sandbox.permission_profile', codux['missing_facts'])

    def test_codex_route_pass_requires_observed_permission_profile_and_all_checks(self):
        observations = {
            'kernel_os': 'linux',
            'host_os': 'android',
            'architecture': 'aarch64',
            'runtime_kind': 'proot',
            'sandbox': {'enabled': True, 'permission_profile': 'workspace-write'},
        }
        results = {
            check_id: True for check_id in (
                'check_artifact_integrity',
                'check_agent_runtime_compatibility',
                'check_agent_version',
                'check_login_and_readonly_task',
                'check_sandbox',
                'check_permission_profile',
            )
        }
        result = evaluate_route(
            self.graph, 'route_codux_community', observations, results,
        )
        self.assertEqual(result['status'], 'pass')

    def test_codex_auth_route_keeps_sandbox_and_profile_gate_when_runtime_unknown(self):
        result = evaluate_route(
            self.graph,
            'route_codex_device_auth_beta',
            {'auth': {'failure_stage': 'localhost_callback'}},
            {
                'check_agent_version': True,
                'check_account_permission': True,
                'check_login_and_readonly_task': True,
                'check_artifact_integrity': True,
                'check_agent_runtime_compatibility': True,
                'check_sandbox': True,
            },
        )
        self.assertNotEqual(result['status'], 'pass')
        self.assertIn('check_permission_profile', result['missing_checks'])
        self.assertEqual(result['applicability']['status'], 'unknown')

    def test_proot_does_not_infer_android_host_from_linux_kernel(self):
        result = evaluate_route(
            self.graph,
            'route_codux_community',
            {'kernel_os': 'linux', 'host_os': None,
             'architecture': 'aarch64', 'runtime_kind': 'proot'},
            {'check_agent_version': True, 'check_sandbox': True},
        )
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['applicability']['missing_facts'], ['host_os'])

    def test_abstract_preservation_strategy_cannot_be_selected_as_a_route(self):
        result = evaluate_route(
            self.graph, 'route_original_artifact',
            {'kernel_os': 'linux', 'host_os': 'android',
             'architecture': 'aarch64', 'runtime_kind': 'proot'},
            {},
        )
        self.assertEqual(result['status'], 'unsupported')

    def test_prime_glibc_route_requires_integrity_environment_and_version_checks(self):
        observation = {
            'kernel_os': 'linux', 'host_os': 'android', 'architecture': 'aarch64',
            'libc': {'family': 'glibc', 'version': '2.35'},
        }
        result = evaluate_route(
            self.graph, 'route_compatible_glibc_userland', observation,
            {'check_agent_version': True},
        )
        self.assertNotEqual(result['status'], 'pass')
        self.assertIn('check_artifact_integrity', result['missing_checks'])
        self.assertIn('check_runtime_compatibility', result['missing_checks'])
        passed = evaluate_route(
            self.graph, 'route_compatible_glibc_userland', observation,
            {
                'check_artifact_integrity': True,
                'check_runtime_compatibility': True,
                'check_agent_version': True,
            },
        )
        self.assertEqual(passed['status'], 'pass')

    def test_ish_playbook_preserves_all_three_agent_targets(self):
        playbook = next(
            p for p in self.graph['recovery_playbooks'] if p['id'] == 'pb_ios_ish_i386'
        )
        self.assertEqual(
            set(playbook['agent_ids']),
            {'agent_codex', 'agent_claude', 'agent_prime'},
        )

    def test_oauth_callback_and_token_exchange_are_separate_branches(self):
        callback = {'os': 'android', 'auth': {'failure_stage': 'localhost_callback'}}
        token = {'os': 'android', 'auth': {'failure_stage': 'token_exchange'}}
        callback_result = evaluate_condition(
            next(p for p in self.graph['recovery_playbooks']
                 if p['id'] == 'pb_codex_oauth_device_auth')['applicability'],
            callback,
        )
        token_result = evaluate_condition(
            next(p for p in self.graph['recovery_playbooks']
                 if p['id'] == 'pb_codex_oauth_device_auth')['applicability'],
            token,
        )
        self.assertEqual(callback_result['status'], 'pass')
        self.assertEqual(token_result['status'], 'fail')

    def test_fixed_prime_release_claims_are_bound_to_recipe(self):
        evidence = json.loads((ROOT / 'catalog' / 'source-evidence.json').read_text())
        recipe = json.loads((ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json').read_text())
        artifact = recipe['artifact']
        claims = {c['id']: c for c in evidence['claims']}
        self.assertEqual(artifact['published_sha256'], claims['claim_prime_archive_digest']['value'])
        self.assertEqual(artifact['size_bytes'], claims['claim_prime_archive_size']['value'])
        self.assertEqual(artifact['libc_min_version'], claims['claim_prime_glibc_min']['value'])
        self.assertIsNone(artifact['observed_sha256'])
        self.assertFalse(artifact['download_verified'])
        for ref in ('src_prime_version_cli', 'src_prime_version_config'):
            self.assertIn(ref, artifact['source_refs'])
        for ref in ('claim_prime_version_stdout', 'claim_prime_version_resolution'):
            self.assertIn(ref, artifact['claim_refs'])

    def test_bound_recipe_rejects_asset_name_or_url_drift(self):
        recipe = load_recipe(ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json')
        for key, value in (
            ('name', '../../outside.txt'),
            ('url', 'https://attacker.invalid/prime-agent.tar.gz'),
        ):
            changed = json.loads(json.dumps(recipe))
            changed['artifact'][key] = value
            with self.subTest(field=key), self.assertRaises(CatalogError):
                validate_recipe(changed, self.graph)

    def test_recipe_rejects_required_checks_without_an_implemented_adapter(self):
        recipe = load_recipe(ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json')
        recipe['required_checks'].append('check_sandbox')
        with self.assertRaises(CatalogError):
            validate_recipe(recipe)


if __name__ == '__main__':
    unittest.main()
