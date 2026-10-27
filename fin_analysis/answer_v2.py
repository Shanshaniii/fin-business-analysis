"""Portable ref-only demonstration; no model transport or semantic acceptance.

The caller owns the trusted registry. Never build that registry from model text.
Financial metadata is copied from registered records, never supplied by an answer.
"""
from copy import deepcopy


def resolve_answer(answer, registry, *, required_tool_refs=None):
    """Resolve an answer and optionally require trusted tool-output citations.

    required_tool_refs belongs to the calling program's verified tool trace,
    never to the answer. Missing citations raise; no answer is auto-completed.
    """
    if not isinstance(answer, dict) or set(answer) != {'facts', 'references'}:
        raise ValueError('answer_requires_facts_and_references_only')
    required = []
    if required_tool_refs is not None:
        if not isinstance(required_tool_refs, (list, tuple)):
            raise ValueError('required_tool_refs_must_be_trusted_id_sequence')
        for ref in required_tool_refs:
            if not isinstance(ref, str) or ref not in registry:
                raise ValueError('unregistered_required_tool_reference')
            if not isinstance(registry[ref], dict) or registry[ref].get('kind') not in {'fact', 'basis'}:
                raise ValueError('required_tool_reference_must_be_financial')
            if ref in required:
                raise ValueError('duplicate_required_tool_reference')
            required.append(ref)
    resolved = {}
    for slot, kinds in (('facts', {'fact', 'basis'}),
                        ('references', {'policy', 'definition', 'formula', 'source'})):
        values = answer[slot]
        if not isinstance(values, list) or len(values) > 64:
            raise ValueError('bounded_reference_array_required')
        rows, seen = [], set()
        for item in values:
            if not isinstance(item, dict) or set(item) != {'ref'}:
                raise ValueError('ref_only_required_no_answer_metadata')
            ref = item['ref']
            if not isinstance(ref, str) or ref not in registry:
                raise ValueError('unregistered_reference')
            if ref in seen:
                raise ValueError('duplicate_reference')
            record = registry[ref]
            if record.get('kind') not in kinds:
                raise ValueError('reference_in_wrong_slot')
            if slot == 'facts' and not all(record.get(k) is not None for k in
                    ('company_code', 'period', 'scope', 'value', 'unit')):
                raise ValueError('incomplete_trusted_financial_record')
            seen.add(ref)
            rows.append({'ref': ref, 'record': deepcopy(record)})
        resolved[slot] = rows
    cited = {row['ref'] for row in resolved['facts']}
    missing = [ref for ref in required if ref not in cited]
    if missing:
        raise ValueError('required_tool_result_not_cited:' + ','.join(missing))
    return {'status': 'reference_contract_valid', 'semantic_acceptance': 'not_evaluated',
            'model_status': 'not_run', **resolved}


def demo(calculation):
    """Construct labelled synthetic evidence from the existing Decimal engine."""
    registry = {}
    for row in calculation['records']:
        for name, metric in row['metrics'].items():
            if metric['status'] != 'ok':
                continue
            ref = 'F' + str(len(registry) + 1)
            registry[ref] = {'kind': 'fact', 'company_code': row['company_code'],
                'period': row['period'], 'scope': row['scope'], 'metric': name,
                'value': metric['display_value'], 'unit': metric['unit'],
                'synthetic': row['synthetic'], 'provenance': 'local Decimal calculation'}
    registry['P1'] = {'kind': 'policy', 'text': '合成规则：经营原因须有独立业务证据。', 'synthetic': True}
    ref = next(iter(registry))
    examples = [
        ('合法 ref-only', {'facts': [{'ref': ref}], 'references': [{'ref': 'P1'}]}, None),
        ('拒绝模型改写期间', {'facts': [{'ref': ref, 'period': '2099-12-31'}], 'references': []}, None),
        ('拒绝政策卡冒充财务事实', {'facts': [{'ref': 'P1'}], 'references': []}, None),
        ('拒绝虚构引用', {'facts': [{'ref': 'UNKNOWN'}], 'references': []}, None),
        ('已引用必需工具产出', {'facts': [{'ref': ref}], 'references': []}, [ref]),
        ('拒绝工具产出未引用', {'facts': [], 'references': [{'ref': 'P1'}]}, [ref]),
    ]
    results = []
    for label, answer, required in examples:
        try:
            outcome = resolve_answer(answer, registry, required_tool_refs=required)
        except ValueError as exc:
            outcome = {'status': 'rejected', 'reason': str(exc), 'model_status': 'not_run'}
        results.append({'label': label, 'input': answer,
                        'required_tool_refs': required, 'outcome': outcome})
    return {'synthetic': True, 'model_status': 'not_run', 'registry': registry,
            'examples': results, 'scope': 'reference shape and slot demonstration; not the full internal inference pipeline'}
