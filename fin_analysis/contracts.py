"""Financial operand contracts, distinct from engineering release versions."""
import json, hashlib
from pathlib import Path
from datetime import date
from decimal import Decimal
KINDS = {'TotalAssets': 'stock', 'TotalLiability': 'stock', 'EndCashEquivalent': 'stock', 'OperatingEvenue': 'flow', 'NetProfit': 'flow', 'ProfitParent': 'flow', 'OperatingCashFlow': 'flow'}
ROLES = {'M01': ('TotalLiability', 'TotalAssets', 'percent'), 'M02': ('NetProfit', 'OperatingEvenue', 'percent'), 'M03': ('OperatingEvenue', 'OperatingEvenue', 'percent'), 'M04N': ('NetProfit', 'NetProfit', 'percent'), 'M04P': ('ProfitParent', 'ProfitParent', 'percent'), 'M05': ('OperatingCashFlow', 'NetProfit', 'times'), 'M06': ('OperatingCashFlow', 'OperatingEvenue', 'percent')}
LABELS = {'TotalAssets': ['资产总计'], 'TotalLiability': ['负债合计'], 'EndCashEquivalent': ['期末现金及现金等价物余额'], 'OperatingEvenue': ['营业收入'], 'NetProfit': ['净利润'], 'ProfitParent': ['归属于母公司股东的净利润'], 'OperatingCashFlow': ['经营活动产生的现金流量净额']}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def operand_identity(op):
    """Fingerprint values and semantic metadata, not storage path of an identical copy."""
    keys = ['source_id', 'source_sha256', 'source_row_id', 'company_code', 'scope', 'currency', 'field_name', 'field_kind', 'period', 'period_start', 'period_kind', 'version']
    value = {k: op.get(k) for k in keys}
    v = op.get('value_CNY')
    value['value_CNY'] = str(Decimal(str(v)).normalize()) if v is not None else None
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def field_error(id, left, right, unit):
    if id not in ROLES:
        return 'unknown_formula'
    n, d, u = ROLES[id]
    if unit != u:
        return 'formula_unit_mismatch'
    if left.get('field_name') != n or right.get('field_name') != d:
        return 'formula_field_mismatch'
    for op in [left, right]:
        expected = KINDS[op['field_name']]
        if op.get('field_kind', expected) != expected:
            return 'stock_flow_mismatch'
    return None

def annual_error(op):
    if op.get('field_name') not in KINDS:
        return 'unknown_field'
    kind = KINDS[op['field_name']]
    if op.get('field_kind', kind) != kind:
        return 'stock_flow_mismatch'
    try:
        end = date.fromisoformat(op['period'])
    except (KeyError, ValueError, TypeError):
        return 'invalid_period_end'
    if (end.month, end.day) != (12, 31):
        return 'nonannual_period_end'
    if kind == 'stock':
        if op.get('period_start') not in ('', None):
            return 'stock_has_flow_interval'
        if op.get('period_kind', 'point_in_time') != 'point_in_time':
            return 'stock_period_kind_mismatch'
        return None
    try:
        start = date.fromisoformat(op['period_start'])
    except (KeyError, ValueError, TypeError):
        return 'missing_or_invalid_flow_start'
    if start != date(end.year, 1, 1) or (end - start).days + 1 not in (365, 366):
        return 'flow_not_full_calendar_year'
    if op.get('period_kind', 'annual') != 'annual':
        return 'flow_period_kind_mismatch'
    return None
