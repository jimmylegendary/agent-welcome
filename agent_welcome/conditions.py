"""Typed predicate validation and three-valued evaluation."""

import re


class ConditionError(ValueError):
    pass


OPERATORS = {'all', 'any', 'eq', 'in', 'version_gte'}
_VERSION = re.compile(r'^[0-9]+(?:\.[0-9]+)*$')


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
    if not isinstance(observations, dict):
        raise ConditionError('observations must be an object')
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
        passed = actual in condition['values']
    else:
        if not isinstance(actual, str):
            raise ConditionError(f'{condition["fact"]} must be a dotted numeric version')
        passed = compare_versions(actual, condition['value']) >= 0
    return {
        'status': 'pass' if passed else 'fail',
        'missing_facts': [],
        'reason': f'{condition["fact"]} {op}',
    }
