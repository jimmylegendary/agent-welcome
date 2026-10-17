"""Load and validate the local knowledge graph and setup recipes."""

import json
import re
from pathlib import Path
from pathlib import PurePosixPath

from .conditions import (
    ConditionError,
    evaluate_condition as _evaluate_condition,
    validate_condition,
)


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_RELATIONS = {
    'requires', 'applies_to', 'excludes', 'candidate_for', 'diagnosed_by',
    'recovered_by', 'verified_by', 'supported_by', 'constrained_by',
    'describes', 'precedes', 'claims',
}


class CatalogError(ValueError):
    pass


def evaluate_condition(condition, observations):
    try:
        return _evaluate_condition(condition, observations)
    except ConditionError as exc:
        raise CatalogError(str(exc)) from exc


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f'cannot read JSON {path}: {exc}') from exc


def load_catalog(path=None):
    data = _read_json(path or ROOT / 'kg' / 'graph.json')
    validate_catalog(data)
    return data


def load_recipe(path_or_id):
    path = Path(path_or_id)
    if not path.exists():
        path = ROOT / 'recipes' / f'{path_or_id}.json'
    recipe = _read_json(path)
    validate_recipe(recipe)
    return recipe


def validate_recipe(recipe, catalog=None):
    if not isinstance(recipe, dict) or recipe.get('schema_version') != '1.0':
        raise CatalogError('recipe schema_version must be 1.0')
    for key in (
        'id', 'version', 'agent_id', 'success_scope', 'applicability', 'artifact',
        'required_checks', 'not_checked', 'retry_budget',
    ):
        if key not in recipe:
            raise CatalogError(f'recipe is missing {key}')
    try:
        validate_condition(recipe['applicability'])
    except ConditionError as exc:
        raise CatalogError(str(exc)) from exc
    artifact = recipe['artifact']
    required = {
        'id', 'name', 'version', 'url', 'target', 'architecture', 'os', 'libc_family',
        'libc_min_version', 'published_sha256', 'size_bytes', 'payload_path',
        'source_refs', 'claim_refs', 'observed_sha256', 'download_verified',
    }
    missing = required - set(artifact)
    if missing:
        raise CatalogError(f'artifact is missing fields: {sorted(missing)}')
    if not artifact['url'].startswith('https://'):
        raise CatalogError('artifact URL must use HTTPS')
    if not re.fullmatch(r'[0-9a-f]{64}', artifact['published_sha256']):
        raise CatalogError('published SHA-256 must be lowercase hex')
    if artifact['observed_sha256'] is not None or artifact['download_verified'] is not False:
        raise CatalogError('unobserved artifact facts must remain null/false')
    if not isinstance(artifact['size_bytes'], int) or artifact['size_bytes'] <= 0:
        raise CatalogError('artifact size_bytes must be positive')
    payload_path = artifact['payload_path']
    if (
        not isinstance(payload_path, str)
        or not payload_path
        or '\\' in payload_path
        or payload_path.startswith('/')
        or any(part in {'', '.', '..'} for part in payload_path.split('/'))
        or (len(payload_path) >= 2 and payload_path[1] == ':')
        or PurePosixPath(payload_path).is_absolute()
    ):
        raise CatalogError('artifact payload_path must be a safe relative path')
    artifact_id = artifact['id']
    if (
        not isinstance(artifact_id, str)
        or not artifact_id
        or '/' in artifact_id
        or '\\' in artifact_id
        or artifact_id in {'.', '..'}
    ):
        raise CatalogError('artifact id must be a single safe path component')
    if recipe['success_scope'] != 'binary_installation':
        raise CatalogError('this reference adapter only declares binary_installation success')
    if artifact['version'] != recipe['version']:
        raise CatalogError('artifact version must match recipe version')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', artifact['libc_min_version']):
        raise CatalogError('artifact libc_min_version must be a dotted numeric version')
    if not isinstance(artifact['source_refs'], list) or not artifact['source_refs'] or not all(
        isinstance(value, str) for value in artifact['source_refs']
    ):
        raise CatalogError('artifact source_refs must be a non-empty list of IDs')
    if not isinstance(artifact['claim_refs'], list) or not artifact['claim_refs'] or not all(
        isinstance(value, str) for value in artifact['claim_refs']
    ):
        raise CatalogError('artifact claim_refs must be a non-empty list of IDs')
    for limit_name in ('max_archive_bytes', 'max_expanded_bytes', 'max_members',
                       'probe_timeout_seconds'):
        if limit_name in artifact and (
            not isinstance(artifact[limit_name], int) or artifact[limit_name] <= 0
        ):
            raise CatalogError(f'artifact {limit_name} must be a positive integer')
    if artifact.get('max_archive_bytes', artifact['size_bytes']) < artifact['size_bytes']:
        raise CatalogError('max_archive_bytes cannot be smaller than published artifact size')
    retry = recipe['retry_budget']
    if (
        not isinstance(retry, dict)
        or not isinstance(retry.get('per_step'), int)
        or not isinstance(retry.get('total'), int)
        or retry['per_step'] <= 0
        or retry['total'] < retry['per_step']
    ):
        raise CatalogError('retry_budget requires positive finite per_step and total values')
    if not isinstance(recipe['required_checks'], list) or 'binary_installation' not in recipe['required_checks']:
        raise CatalogError('recipe must require binary_installation verification')
    if not isinstance(recipe['not_checked'], list):
        raise CatalogError('not_checked must be a list')
    if catalog is not None:
        sources_by_id = {source['id']: source for source in catalog.get('sources', [])}
        source_ids = set(sources_by_id)
        claim_by_id = {claim['id']: claim for claim in catalog.get('claims', [])}
        node_by_id = {node['id']: node for node in catalog.get('nodes', [])}
        if recipe['agent_id'] not in node_by_id or node_by_id[recipe['agent_id']].get('type') != 'agent':
            raise CatalogError('recipe agent_id is not bound to a graph agent')
        for source_id in artifact['source_refs']:
            if source_id not in source_ids:
                raise CatalogError(f'artifact references unknown source {source_id}')
            if sources_by_id[source_id].get('evidence_status') != 'pinned_source':
                raise CatalogError(f'artifact source {source_id} is not pinned executable evidence')
        for claim_id in artifact['claim_refs']:
            if claim_id not in claim_by_id:
                raise CatalogError(f'artifact references unknown claim {claim_id}')
            if claim_by_id[claim_id]['source_id'] not in artifact['source_refs']:
                raise CatalogError(f'artifact claim {claim_id} is not bound to one of its sources')
            claim = claim_by_id[claim_id]
            expected = {
                'published_sha256': artifact['published_sha256'],
                'published_size_bytes': artifact['size_bytes'],
                'libc.family': artifact['libc_family'],
                'libc.version_gte': artifact['libc_min_version'],
            }.get(claim['predicate'])
            if expected is not None and claim['value'] != expected:
                raise CatalogError(f'artifact disagrees with pinned claim {claim_id}')
        graph_artifact = next(
            (node for node in catalog.get('nodes', [])
             if node.get('artifact_id') == artifact['id']),
            None,
        )
        if not graph_artifact:
            raise CatalogError('recipe artifact has no structured KG artifact node')
        for field in ('version', 'target', 'architecture', 'os', 'libc_family',
                      'libc_min_version', 'published_sha256', 'size_bytes'):
            if graph_artifact.get(field) != artifact.get(field):
                raise CatalogError(f'recipe artifact disagrees with KG field {field}')


def validate_catalog(data):
    if not isinstance(data, dict) or data.get('schema_version') != '0.2':
        raise CatalogError('catalog schema_version must be 0.2')
    if data.get('runtime_tested') is not False or data.get('direct_reproduction') is not False:
        raise CatalogError('research graph must not claim unobserved runtime success')
    if data.get('automatic_execution_enabled') is not False:
        raise CatalogError('research graph cannot enable automatic execution')
    for key in ('nodes', 'links', 'sources', 'claims', 'recovery_playbooks'):
        if not isinstance(data.get(key), list):
            raise CatalogError(f'catalog {key} must be a list')
    node_ids = [node.get('id') for node in data['nodes']]
    if None in node_ids or len(set(node_ids)) != len(node_ids):
        raise CatalogError('node ids must be present and unique')
    node_by_id = {node['id']: node for node in data['nodes']}
    source_ids = {source.get('id') for source in data['sources']}
    if None in source_ids or len(source_ids) != len(data['sources']):
        raise CatalogError('source ids must be present and unique')
    claim_ids = {claim.get('id') for claim in data['claims']}
    claim_by_id = {claim['id']: claim for claim in data['claims']}
    if None in claim_ids or len(claim_ids) != len(data['claims']):
        raise CatalogError('claim ids must be present and unique')
    for claim in data['claims']:
        if claim.get('source_id') not in source_ids:
            raise CatalogError(f'claim {claim.get("id")} has unknown source')
    for source in data['sources']:
        if source.get('legacy') is True and source.get('evidence_status') != 'legacy_unresolved':
            raise CatalogError(f'legacy source {source["id"]} must remain unresolved')
        if source.get('legacy') is False and source.get('evidence_status') != 'pinned_source':
            raise CatalogError(f'pinned source {source["id"]} has invalid evidence status')
        digest = source.get('content_sha256')
        if digest is not None and not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise CatalogError(f'source {source["id"]} has malformed content SHA-256')
    for node in data['nodes']:
        for ref in node.get('source_refs', []):
            if ref not in source_ids:
                raise CatalogError(f'node {node["id"]} has unknown source {ref}')
    for link in data['links']:
        if link.get('source') not in node_by_id or link.get('target') not in node_by_id:
            raise CatalogError(f'link {link.get("id")} has unknown endpoint')
        if link.get('relation') not in ALLOWED_RELATIONS:
            raise CatalogError(f'link {link.get("id")} has uncontrolled relation')
        if not link.get('details', {}).get('original_relation'):
            raise CatalogError(f'link {link.get("id")} lost original relation')
        for ref in link.get('source_refs', []):
            if ref not in source_ids:
                raise CatalogError(f'link {link.get("id")} has unknown source {ref}')
    for node in data['nodes']:
        if 'applicability' in node:
            try:
                validate_condition(node['applicability'])
            except ConditionError as exc:
                raise CatalogError(f'node {node["id"]}: {exc}') from exc
        for check_id in node.get('required_check_ids', []):
            if check_id not in node_by_id or node_by_id[check_id].get('type') != 'success_check':
                raise CatalogError(f'node {node["id"]} has unresolved required check {check_id}')
        for claim_id in node.get('claim_refs', []):
            if claim_id not in claim_ids:
                raise CatalogError(f'node {node["id"]} has unknown claim {claim_id}')
            if claim_by_id[claim_id]['source_id'] not in node.get('source_refs', []):
                raise CatalogError(f'node {node["id"]} has an unbound claim source {claim_id}')
            bound = any(
                link.get('source') == node['id']
                and link.get('target') == claim_id
                and link.get('relation') == 'supported_by'
                for link in data['links']
            )
            if not bound:
                raise CatalogError(f'node {node["id"]} has no supported_by edge to {claim_id}')
        if node.get('type') == 'claim' and node.get('source_id') not in source_ids:
            raise CatalogError(f'claim node {node["id"]} has unknown source')
        if node.get('abstract') and (
            node.get('agent_id') is not None or node.get('required_check_ids')
        ):
            raise CatalogError(f'abstract route {node["id"]} cannot be executable')
    for playbook in data['recovery_playbooks']:
        for key in ('id', 'agent_id', 'symptom_id', 'diagnostic_ids',
                    'route_ids', 'required_check_ids', 'applicability'):
            if key not in playbook:
                raise CatalogError(f'playbook is missing {key}')
        if playbook['agent_id'] not in node_by_id or node_by_id[playbook['agent_id']].get('type') != 'agent':
            raise CatalogError(f'playbook {playbook["id"]} has unresolved agent')
        agent_ids = playbook.get('agent_ids', [playbook['agent_id']])
        if not isinstance(agent_ids, list) or not agent_ids:
            raise CatalogError(f'playbook {playbook["id"]} agent_ids must be a non-empty list')
        for agent_id in agent_ids:
            if agent_id not in node_by_id or node_by_id[agent_id].get('type') != 'agent':
                raise CatalogError(f'playbook {playbook["id"]} has unresolved agent {agent_id}')
        if playbook['symptom_id'] not in node_by_id or node_by_id[playbook['symptom_id']].get('type') != 'symptom':
            raise CatalogError(f'playbook {playbook["id"]} has unresolved symptom')
        for key, expected_type in (
            ('diagnostic_ids', 'diagnostic'),
            ('route_ids', None),
            ('required_check_ids', 'success_check'),
        ):
            if not isinstance(playbook[key], list):
                raise CatalogError(f'playbook {playbook["id"]} {key} must be a list')
            for ref in playbook[key]:
                if ref not in node_by_id:
                    raise CatalogError(f'playbook {playbook["id"]} has unresolved {key}: {ref}')
                if expected_type and node_by_id[ref].get('type') != expected_type:
                    raise CatalogError(f'playbook {playbook["id"]} {ref} has wrong node type')
        try:
            validate_condition(playbook['applicability'])
        except ConditionError as exc:
            raise CatalogError(f'playbook {playbook["id"]}: {exc}') from exc
        for ref in playbook.get('source_refs', []):
            if ref not in source_ids:
                raise CatalogError(f'playbook {playbook["id"]} has unknown source {ref}')
    return True


def evaluate_route(catalog, route_id, observations, check_results):
    nodes = {node['id']: node for node in catalog['nodes']}
    route = nodes.get(route_id)
    if not route:
        raise CatalogError(f'unknown route: {route_id}')
    if route.get('type') not in {'community_route', 'preservation_route',
                                 'modified_artifact_route', 'recovery_candidate'}:
        raise CatalogError(f'node is not a route: {route_id}')
    if route.get('abstract'):
        return {
            'status': 'unsupported',
            'route_id': route_id,
            'reason': 'abstract preservation strategy has no executable agent binding',
            'required_checks': [],
            'missing_checks': [],
            'failed_checks': [],
        }
    condition = route.get('applicability', {'op': 'all', 'conditions': [
        {'op': 'eq', 'fact': 'route.selected', 'value': route_id}
    ]})
    applicability = evaluate_condition(condition, observations)
    required = list(route.get('required_check_ids', []))
    if route.get('agent_id') == 'agent_codex' and observations.get('runtime_kind') == 'proot':
        if 'check_sandbox' not in required:
            required.append('check_sandbox')
    missing = []
    failed = []
    for check_id in required:
        value = check_results.get(check_id)
        status = value.get('status') if isinstance(value, dict) else (
            'pass' if value is True else 'fail' if value is False else None
        )
        if status is None or status == 'unknown':
            missing.append(check_id)
        elif status != 'pass':
            failed.append(check_id)
    outcome = 'pass' if applicability['status'] == 'pass' and not missing and not failed else (
        'fail' if applicability['status'] == 'fail' or failed else 'unknown'
    )
    return {
        'status': outcome,
        'route_id': route_id,
        'applicability': applicability,
        'required_checks': required,
        'missing_checks': missing,
        'failed_checks': failed,
    }
