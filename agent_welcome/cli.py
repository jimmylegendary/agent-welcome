"""Command-line interface for validating and running local setup recipes."""

import argparse
import json
import sys
from pathlib import Path

from .catalog import (
    CatalogError,
    ROOT,
    evaluate_condition,
    load_catalog,
    load_recipe,
    validate_recipe,
)
from .environment import observe
from .runner import RunError, _eligibility_status, resume, start, status


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _diagnose(recipe, observations):
    result = evaluate_condition(recipe['applicability'], observations)
    if result['status'] == 'pass':
        status_name = 'READY'
    else:
        status_name, _ = _eligibility_status(recipe, observations)
    return {
        'recipe_id': recipe['id'],
        'status': status_name,
        'condition': result,
        'success_scope': recipe['success_scope'],
        'required_checks': recipe.get('required_checks', []),
        'not_checked': recipe.get('not_checked', []),
        'observation_provenance': observations.get('provenance', {}),
    }


def _load_bound_recipe(recipe_id):
    graph = load_catalog()
    recipe = load_recipe(recipe_id)
    validate_recipe(recipe, graph)
    return recipe


def _parser():
    parser = argparse.ArgumentParser(prog='python -m agent_welcome')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='validate the local graph and recipe data')
    diagnose = commands.add_parser('diagnose', help='evaluate a recipe against observations')
    diagnose.add_argument('--recipe', required=True)
    diagnose.add_argument('--observations', help='JSON observation file; diagnose only')
    start_parser = commands.add_parser('start', help='create or continue a setup run')
    start_parser.add_argument('--recipe', required=True)
    start_parser.add_argument('--state-dir', required=True)
    start_input = start_parser.add_mutually_exclusive_group()
    start_input.add_argument('--artifact-file')
    start_input.add_argument('--download', action='store_true')
    resume_parser = commands.add_parser('resume', help='resume a saved setup run')
    resume_parser.add_argument('--state-dir', required=True)
    resume_input = resume_parser.add_mutually_exclusive_group()
    resume_input.add_argument('--artifact-file')
    resume_input.add_argument('--download', action='store_true')
    resume_parser.add_argument(
        '--user-action-completed',
        action='store_true',
        help='acknowledge a user wait; does not verify credentials or mark success',
    )
    status_parser = commands.add_parser('status', help='read a saved setup state')
    status_parser.add_argument('--state-dir', required=True)
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate':
            graph = load_catalog()
            recipe_path = ROOT / 'recipes' / 'prime-agent-0.10.0-linux-arm64.json'
            recipe = load_recipe(recipe_path)
            validate_recipe(recipe, graph)
            print(_json({
                'status': 'VALID',
                'schema_version': graph['schema_version'],
                'nodes': len(graph['nodes']),
                'links': len(graph['links']),
                'playbooks': len(graph['recovery_playbooks']),
                'recipes': [recipe['id']],
            }))
            return 0
        if args.command == 'diagnose':
            recipe = _load_bound_recipe(args.recipe)
            if args.observations:
                observations = json.loads(Path(args.observations).read_text(encoding='utf-8'))
                if not isinstance(observations, dict):
                    raise CatalogError('observation JSON must contain an object')
            else:
                observations = observe()
            print(_json(_diagnose(recipe, observations)))
            return 0
        if args.command == 'start':
            recipe = _load_bound_recipe(args.recipe)
            result = start(
                recipe, args.state_dir, observation=observe(),
                artifact_file=args.artifact_file, download=args.download,
            )
            print(_json(result))
            return 0
        if args.command == 'resume':
            saved = status(args.state_dir)
            recipe = _load_bound_recipe(saved['recipe_id'])
            result = resume(
                recipe, args.state_dir, observation=observe(),
                artifact_file=args.artifact_file, download=args.download,
                user_action_completed=args.user_action_completed,
            )
            print(_json(result))
            return 0
        if args.command == 'status':
            print(_json(status(args.state_dir)))
            return 0
    except (CatalogError, RunError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(_json({'error': str(exc)}), file=sys.stderr)
        return 2
    return 2
