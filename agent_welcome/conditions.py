"""Typed predicate validation and three-valued evaluation."""

import re


class ConditionError(ValueError):
    pass


OPERATORS = {'all', 'any', 'eq', 'in', 'version_gte'}
_VERSION = re.compile(r'^[0-9]+(?:\.[0-9]+)*$')
_STRING_FACTS = {'kernel_os', 'host_os', 'architecture', 'runtime_kind'}


def validate_observations(observations):
    """Validate known fact types while leaving absent/null facts unknown."""
    if not isinstance(observations, dict):
        raise ConditionError('observations must be an object')
    for key in _STRING_FACTS:
        if key in observations and observations[key] is not None and not isinstance(observations[key], str):
            raise ConditionError(f'observations.{key} must be a string or null')
    for key in ('libc', 'capabilities', 'auth', 'provenance', 'sandbox'):
        if key in observations and observations[key] is not None and not isinstance(observations[key], dict):
            raise ConditionError(f'observations.{key} must be an object or null')
    libc = observations.get('libc')
    if isinstance(libc, dict):
        for key in ('family', 'version'):
            value = libc.get(key)
            if value is not None and not isinstance(value, str):
                raise ConditionError(f'observations.libc.{key} must be a string or null')
        version = libc.get('version')
        if version is not None and not _VERSION.fullmatch(version):
            raise ConditionError('observations.libc.version must be a dotted numeric version')
    capabilities = observations.get('capabilities')
    if isinstance(capabilities, dict):
        for key in ('user_namespace', 'bubblewrap'):
            value = capabilities.get(key)
            if value is not None and not isinstance(value, bool):
                raise ConditionError(f'observations.capabilities.{key} must be a boolean or null')
    auth = observations.get('auth')
    if isinstance(auth, dict):
        stage = auth.get('failure_stage')
        if stage is not None and not isinstance(stage, str):
            raise ConditionError('observations.auth.failure_stage must be a string or null')
        allowed = auth.get('device_code_allowed')
        if allowed is not None and not isinstance(allowed, bool):
            raise ConditionError('observations.auth.device_code_allowed must be a boolean or null')
    sandbox = observations.get('sandbox')
    if isinstance(sandbox, dict):
        for key in ('enabled',):
            value = sandbox.get(key)
            if value is not None and not isinstance(value, bool):
                raise ConditionError(f'observations.sandbox.{key} must be a boolean or null')
        for key in ('backend', 'permission_profile'):
            value = sandbox.get(key)
            if value is not None and not isinstance(value, str):
                raise ConditionError(f'observations.sandbox.{key} must be a string or null')
    return observations


def _version_parts(value):
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise ConditionError(f'malformed numeric version: {value!r}')
    return tuple(int(part) for part in value.split('.'))


def compare_versions(left, right):
    a = _version_parts(left)
    b = _version_parts(right)
    size = max(len(a), len(b))
    a += (0,) * (size - len(a))
    b += (0,) * (size - len(b))
    return (a > b) - (a < b)


def validate_condition(condition):
    if not isinstance(condition, dict):
        raise ConditionError('condition must be an object')
    op = condition.get('op')
    if not isinstance(op, str) or op not in OPERATORS:
        raise ConditionError(f'unsupported condition operator: {op!r}')
    if op in {'all', 'any'}:
        if set(condition) != {'op', 'conditions'}:
            raise ConditionError(f'{op} requires only op and conditions')
        children = condition['conditions']
        if not isinstance(children, list) or not children:
            raise ConditionError(f'{op}.conditions must be a non-empty list')
        for child in children:
            validate_condition(child)
        return
    required = {'op', 'fact', 'value'} if op in {'eq', 'version_gte'} else {'op', 'fact', 'values'}
    if set(condition) != required:
        raise ConditionError(f'{op} has missing or unexpected fields')
    if not isinstance(condition['fact'], str) or not condition['fact']:
        raise ConditionError(f'{op}.fact must be a non-empty string')
    if op == 'version_gte':
        _version_parts(condition['value'])
    elif op == 'eq':
        if not isinstance(condition['value'], (str, int, float, bool, type(None))):
            raise ConditionError('eq.value must be a JSON scalar')
    else:
        values = condition['values']
        if not isinstance(values, list) or not values:
            raise ConditionError('in.values must be a non-empty list')
        if any(not isinstance(v, (str, int, float, bool, type(None))) for v in values):
            raise ConditionError('in.values must contain JSON scalars')


def _lookup(observations, path):
    value = observations
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value or value[part] is None:
            return False, None
        value = value[part]
    return True, value


def evaluate_condition(condition, observations):
    """Return status pass/fail/unknown without converting missing facts to false."""
    validate_condition(condition)
    validate_observations(observations)
    op = condition['op']
    if op in {'all', 'any'}:
        results = [evaluate_condition(child, observations) for child in condition['conditions']]
        missing = sorted({fact for result in results for fact in result['missing_facts']})
        if op == 'all':
            status = 'fail' if any(r['status'] == 'fail' for r in results) else (
                'pass' if all(r['status'] == 'pass' for r in results) else 'unknown'
            )
        else:
            status = 'pass' if any(r['status'] == 'pass' for r in results) else (
                'fail' if all(r['status'] == 'fail' for r in results) else 'unknown'
            )
        return {'status': status, 'missing_facts': missing, 'reason': op}
    found, actual = _lookup(observations, condition['fact'])
    if not found:
        return {
            'status': 'unknown',
            'missing_facts': [condition['fact']],
            'reason': f'missing fact: {condition["fact"]}',
        }
    if not isinstance(actual, (str, int, float, bool, type(None))):
        raise ConditionError(f'{condition["fact"]} must be a JSON scalar')
    if op == 'eq':
        if type(actual) is not type(condition['value']):
            raise ConditionError(f'{condition["fact"]} has an unexpected value type')
        passed = actual == condition['value']
    elif op == 'in':
        if not any(type(actual) is type(candidate) for candidate in condition['values']):
            raise ConditionError(f'{condition["fact"]} has an unexpected value type')
        passed = any(
            type(actual) is type(candidate) and actual == candidate
            for candidate in condition['values']
        )
    else:
        if not isinstance(actual, str):
            raise ConditionError(f'{condition["fact"]} must be a dotted numeric version')
        passed = compare_versions(actual, condition['value']) >= 0
    return {
        'status': 'pass' if passed else 'fail',
        'missing_facts': [],
        'reason': f'{condition["fact"]} {op}',
    }
