"""Portable Decimal engine derived from the r02-v3 calculation contracts.
Synthetic inputs are explicit; real comparability requires separate review.
"""
import json
from pathlib import Path
from datetime import date
from decimal import Decimal, localcontext
from .contracts import KINDS, field_error, annual_error
METRICS={'M01':('debt_ratio','TotalLiability','TotalAssets','percent'),'M02':('net_margin','NetProfit','OperatingEvenue','percent'),'M03':('revenue_growth','OperatingEvenue',None,'percent'),'M04N':('profit_growth','NetProfit',None,'percent'),'M04P':('parent_profit_growth','ProfitParent',None,'percent'),'M05':('cash_profit_ratio','OperatingCashFlow','NetProfit','times'),'M06':('cash_revenue_ratio','OperatingCashFlow','OperatingEvenue','percent')}

def load(path):
 data=json.loads(Path(path).read_text(encoding='utf-8-sig'));records={}
 for row in data['records']:
  end=date.fromisoformat(row['period'])
  if end.month!=12 or end.day!=31:raise ValueError('annual_year_end_required')
  if row['currency']!='CNY' or row['raw_unit']!='CNY' or row['scope'] not in ('consolidated','parent'):raise ValueError('unsupported_unit_currency_scope')
  key=(row['company_code'],row['period'])
  if key in records:raise ValueError('duplicate_company_period')
  for v in row['fields'].values():
   if v is not None and not Decimal(str(v)).is_finite():raise ValueError('nonfinite_input')
  if set(row['fields'])-set(KINDS):raise ValueError('unknown_field')
  records[key]=row
 return data,records

def operand(row,field):
 return {'company_code':row['company_code'],'scope':row['scope'],'currency':row['currency'],'period':row['period'],'field_name':field,'field_kind':KINDS[field],'period_kind':'annual' if KINDS[field]=='flow' else 'point_in_time','period_start':row['period'][:4]+'-01-01' if KINDS[field]=='flow' else '', 'value_CNY':row['fields'].get(field),'source_id':row['source_id'],'version':row['report_version']}

def calculate(data,records,row):
 metrics={};year=int(row['period'][:4]);previous=records.get((row['company_code'],str(year-1)+'-12-31'))
 for fid,(name,num,den,unit) in METRICS.items():
  a=operand(row,num);b=operand(row,den) if den else operand(previous,num) if previous else None
  status='ok';value=None;reason=None
  if b is None or a['value_CNY'] is None or b['value_CNY'] is None:status='missing_operand'
  elif field_error(fid,a,b,unit):status='incompatible_fields'
  elif any(annual_error(x) for x in (a,b)):status='incompatible_period'
  elif any(a[k]!=b[k] for k in ('company_code','scope','currency')):status='incompatible_entity_scope_currency'
  elif den and a['period']!=b['period']:status='incompatible_period'
  elif not den and not (data.get('synthetic') is True and row.get('comparability',{}).get('status')=='synthetic_comparable' and row['comparability'].get('previous_year')==year-1):status='accounting_basis_unverified'
  else:
   av=Decimal(str(a['value_CNY']));bv=Decimal(str(b['value_CNY']))
   if bv==0:status='zero_denominator'
   elif not den and bv<0:status='negative_base_absolute_change_only';reason=str(av-bv)
   elif fid=='M01' and (av<0 or bv<0):status='invalid_balance_sheet_value'
   else:
    with localcontext() as ctx:
     ctx.prec=40;value=(av/bv if den else (av-bv)/bv)*(100 if unit=='percent' else 1)
  metrics[name]={'formula_id':fid,'status':status,'exact_decimal':str(value) if value is not None else None,'display_value':str(value.quantize(Decimal('0.01'))) if value is not None else None,'unit':'%' if unit=='percent' else '倍','operands':[a,b],'reason':reason,'interpretation':'arithmetic_only' if fid!='M05' or b is None or b['value_CNY'] is None or Decimal(str(b['value_CNY']))>=0 else 'suspended_nonpositive_profit'}
 return {'company_code':row['company_code'],'name':row['name'],'period':row['period'],'scope':row['scope'],'synthetic':data.get('synthetic') is True,'metrics':metrics,'cause_status':'not_established','risk_conclusion':None,'model_status':'not_run','limitations':['净现金流不等于销售收款；归母利润不等于母公司单体利润。','真实同比需要核定可比会计基期；本 demo 的可比性仅属于合成样例。','计算结果不能替代经营原因、舞弊或信用风险的证据。']}

def run(path):
 data,records=load(path)
 return {'status':'demo','model_status':'not_run','records':[calculate(data,records,row) for row in records.values()]}
