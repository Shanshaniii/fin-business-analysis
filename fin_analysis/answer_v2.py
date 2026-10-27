"""Portable ref-only demonstration; no model transport or semantic acceptance.

The caller owns the trusted registry. Never build that registry from model text.
Financial metadata is copied from registered records, never supplied by an answer.
"""
from copy import deepcopy


def resolve_answer(answer, registry):
    if not isinstance(answer, dict) or set(answer) != {'facts', 'references'}:
        raise ValueError('answer_requires_facts_and_references_only')
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
        ('合法 ref-only', {'facts': [{'ref': ref}], 'references': [{'ref': 'P1'}]}),
        ('拒绝模型改写期间', {'facts': [{'ref': ref, 'period': '2099-12-31'}], 'references': []}),
        ('拒绝政策卡冒充财务事实', {'facts': [{'ref': 'P1'}], 'references': []}),
        ('拒绝虚构引用', {'facts': [{'ref': 'UNKNOWN'}], 'references': []}),
    ]
    results = []
    for label, answer in examples:
        try:
            outcome = resolve_answer(answer, registry)
        except ValueError as exc:
            outcome = {'status': 'rejected', 'reason': str(exc), 'model_status': 'not_run'}
        results.append({'label': label, 'input': answer, 'outcome': outcome})
    return {'synthetic': True, 'model_status': 'not_run', 'registry': registry,
            'examples': results, 'scope': 'reference shape and slot demonstration; not the full internal inference pipeline'}
