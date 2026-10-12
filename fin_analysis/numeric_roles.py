"""Typed per-occurrence numeric provenance. Source constants are not company outcomes."""
import re
from decimal import Decimal
NUMBER=re.compile(r'(?<![A-Za-z0-9_])[-+]?[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?(?=$|[^A-Za-z0-9_]|CNY\b|USD\b|EUR\b)')
CN_QUANTITY=re.compile(r'[零〇一二三四五六七八九十百千万亿点]+\s*(?:CNY|元|美元|%|％|倍|个百分点)')
BUSINESS_RESULT=re.compile(r'(?:公司|企业|集团|本期|净利润|归母|营业收入|现金流|资产负债率|净利率|同比|增速).{0,20}(?:增长|增加|下降|提升|降低|为|达到|变为).{0,12}[-+]?[0-9]+(?:\.[0-9]+)?\s*(?:%|％|CNY|元|倍|个百分点)')


# All financial number spellings enter one occurrence gate. Unknown spellings fail closed.
NUMERIC_TRANSLATION=str.maketrans('０１２３４５６７８９壹贰叁肆伍陆柒捌玖拾佰仟萬億貳參陸負點圓圆','0123456789一二三四五六七八九十百千万亿二三六负点元元')
def normalize_spelling(text):return text.translate(NUMERIC_TRANSLATION)
CN_CALENDAR=re.compile(r'[零〇一二两三四五六七八九十百千万亿]+(?=年|月|日)')
CN_NUMBER=re.compile(r'(?:百分之|千分之)?[负正]?[零〇一二两三四五六七八九十百千万亿点]+(?=\s*(?:CNY|人民币元|元|美元|万元|亿元|%|％|倍|个百分点|个基点))|(?:百分之|千分之)[负正]?[零〇一二两三四五六七八九十百千万亿点0-9.]+')
DIGITS=dict(zip('零〇一二两三四五六七八九',[0,0,1,2,2,3,4,5,6,7,8,9]))
def decimal_token(token):
 token=token.replace(',','');token=re.sub(r'^(百分之|千分之)','',token)
 if re.fullmatch(r'[-+]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',token):return Decimal(token)
 sign=-1 if token.startswith('负') else 1;token=token.lstrip('负正');parts=token.split('点')
 def integer(s):
  if s.isdigit():return int(s)
  if all(c in DIGITS for c in s):return int(''.join(str(DIGITS[c]) for c in s))
  total=section=n=0
  for c in s:
   if c in DIGITS:n=DIGITS[c]
   elif c in '十百千':section+=(n or 1)*{'十':10,'百':100,'千':1000}[c];n=0
   elif c in '万亿':section+=n;total+=(section or 1)*{'万':10000,'亿':100000000}[c];section=n=0
   else:raise ValueError('unsupported_numeric_spelling')
  return total+section+n
 value=Decimal(integer(parts[0]))
 if len(parts)==2:value+=Decimal('0.'+''.join(str(DIGITS[c]) if c in DIGITS else c if c.isdigit() else 'invalid' for c in parts[1]))
 return sign*value

def occurrences(text):
 text=normalize_spelling(text)
 matches=list(CN_NUMBER.finditer(text))+list(CN_CALENDAR.finditer(text))
 matches += [m for m in NUMBER.finditer(text) if not any(c.start()<=m.start() and m.end()<=c.end() for c in matches)]
 return sorted(matches,key=lambda m:m.start())

METRIC_NAMES={
 'debt_ratio':['期末资产负债率','合并资产负债率','资产负债率'],
 'net_margin':['合并净利润营业收入比','净利率'],
 'revenue_growth':['营业收入同比','收入同比','营收同比'],
 'profit_growth':['合并净利润同比','净利润同比'],
 'parent_profit_growth':['归母净利润同比','归属于母公司股东净利润同比'],
 'cash_profit_ratio':['经营现金净流量净利润比','经营现金净额合并净利润比','经营现金流净额合并净利润比'],
 'cash_revenue_ratio':['经营现金净流量营业收入比','经营现金净额营业收入比','经营现金流净额营业收入比']}
def local_metric(text,start,p):
 sentence=re.split(r'[。；;\n]',text[:start])[-1]
 prefix=re.split(r'[,，、]',sentence)[-1]
 matches=[]
 for metric,names in METRIC_NAMES.items():
  for name in names:
   for m in re.finditer(re.escape(name),prefix):matches.append((m.start(),m.end(),metric))
 # The closest explicitly named indicator controls each occurrence; nested aliases use longest match.
 if not matches:return False
 outer=[m for m in matches if not any(n[0]<=m[0] and n[1]>=m[1] and n[:2]!=m[:2] for n in matches)]
 chosen=max(outer,key=lambda m:(m[1],m[1]-m[0]))
 if chosen[2]!=p['metric']:return False
 context=prefix[:chosen[0]]
 tail=re.split(r'[,，、。；;\n]',text[start:])[0]
 explicit_years=re.findall(r'(20[0-9]{2})(?:年|-[0-9]{2}-[0-9]{2})',sentence+tail)
 if explicit_years and explicit_years[-1]!=p['period'][:4]:return False
 if re.search(r'母公司(?:单体|报表|口径)|单体报表',tail):return False
 for company,code in [('美的','000333'),('贵州茅台','600519'),('茅台','600519'),('中国建筑','601668')]:
  if company in tail and p.get('_company_code') and p['_company_code']!=code:return False
 years=re.findall(r'(20[0-9]{2})年',sentence)
 if years and years[-1]!=p['period'][:4]:return False
 if re.search(r'母公司(?:单体|报表|口径)|单体报表',sentence):return False
 if '归母' in prefix[chosen[1]:] and p['metric']!='parent_profit_growth':return False
 for company,code in [('美的','000333'),('贵州茅台','600519'),('茅台','600519'),('中国建筑','601668')]:
  if company in sentence and p.get('_company_code') and p['_company_code']!=code:return False
 unit=re.match(r'\s*(%|％|倍|CNY|人民币元|万元|亿元|元|美元|个百分点|个基点)',text[start:])
 return True

def add_spans(spans,text,pattern,role):
 for m in re.finditer(pattern,text):spans.append({'start':m.start(),'end':m.end(),'role':role,'source_text':m.group()})

def policy_spans(text,p):
 spans=[];name=p['policy_name'];add_spans(spans,text,re.escape(name),'policy_identifier')
 numbers=re.findall(r'[0-9]+',name)
 for n in numbers:add_spans(spans,text,r'解释第'+re.escape(n)+r'号','policy_identifier')
 iso=p['effective_date'];year,month,day=iso.split('-');dates=[iso,year+'年'+str(int(month))+'月'+str(int(day))+'日',year+'年']
 for date in dates:
  d=re.escape(date)
  add_spans(spans,text,r'(?:生效|施行|实施|执行|适用)(?:日期|日|时间)?(?:为|是|于|自|从)?\s*'+d,'policy_effective_date')
  add_spans(spans,text,r'(?:自|从|于)?'+d+r'(?:起|开始)?(?:生效|施行|实施|执行|适用)','policy_effective_date')
  add_spans(spans,text,d+r'(?:，|,|年)?(?:该)?(?:会计)?(?:政策|解释)?(?:生效|施行|实施|执行|适用)','policy_effective_date')
 for page in p.get('pdf_pages',[]):add_spans(spans,text,r'(?:PDF|pdf)(?:第)?\s*'+re.escape(str(page))+r'页','policy_source_page')
 return spans

def formula_spans(text,p):
 expected=p['formula'];parts=re.findall(r'[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:\.[0-9]+)?|[^\s]',expected)
 pattern=r'\s*'.join('[*×]' if token=='*' else '[/÷]' if token=='/' else re.escape(token) for token in parts)+r'(?!\s*[%％元]|\s*(?:CNY|USD|EUR)\b)'
 spans=[];add_spans(spans,text,pattern,'registered_formula_expression')
 constants=re.findall(r'[0-9]+(?:\.[0-9]+)?',expected)
 for n in constants:add_spans(spans,text,r'(?:公式常量|乘数|换算常数)\s*(?:为|是|=)?\s*'+re.escape(n)+r'(?!\s*[%％元]|[0-9]|\s*(?:CNY|USD|EUR)\b)','formula_constant_role')
 return spans

def check(text,kind,p,partial=False):
 text=normalize_spelling(text)
 spans=[]
 if kind=='policy':spans=policy_spans(text,p)
 elif kind=='formula':spans=formula_spans(text,p)
 elif kind=='definition':pass
 elif kind=='source':
  provenance=p['provenance'];page=provenance.get('pdf_page')
  if page is not None:add_spans(spans,text,r'(?:PDF|pdf)(?:第)?\s*'+re.escape(str(page))+r'页','source_document_page')
  row=provenance.get('source_row_id')
  if row:add_spans(spans,text,re.escape(row),'source_row_identifier')
  date=provenance.get('period')
  if date:add_spans(spans,text,r'(?:字段|来源)(?:期间|日期)为?'+re.escape(date),'source_period_metadata')
 elif kind=='fact':
  # Exact period/year has a calendar role; each result must equal this metric and occur in its named statement.
  year=p['period'][:4];add_spans(spans,text,re.escape(p['period']),'metric_period');add_spans(spans,text,re.escape(year)+r'年','metric_period')
  value=Decimal(p['display_value']);name=re.sub(r'^20[0-9]{2}年','',p['display_name'])
  for m in occurrences(text):
   if any(s['start']<=m.start() and m.end()<=s['end'] for s in spans):continue
   if decimal_token(m.group())!=value:continue
   if m.group().startswith('千分之'):continue
   clause=re.split(r'[。；;]',text[:m.start()])[-1]
   unit_suffix=re.match(r'\s*(%|％|倍|CNY|元|万元|亿元)',text[m.end():])
   if unit_suffix and unit_suffix.group(1) not in (p['unit_label'],'％' if p['unit_label']=='%' else p['unit_label']):continue
   if local_metric(text,m.start(),p) and (unit_suffix or m.group().startswith('百分之')):spans.append({'start':m.start(),'end':m.end(),'role':'registered_metric_result','source_text':m.group()})
 elif kind=='basis':
  spans=policy_spans(text,p['accounting_policy_evidence'])
  for date in (p['current_period'],p['growth_base_period']):
   add_spans(spans,text,re.escape(date),'basis_period');add_spans(spans,text,re.escape(date[:4])+r'年','basis_period')
  amounts={Decimal(p[k]) for k in ('selected_current_CNY','original_base_CNY','adjusted_base_CNY')}
  for m in occurrences(text):
   if decimal_token(m.group()) not in amounts:continue
   suffix=text[m.end():m.end()+12]
   if re.match(r'\s*(?:%|％|倍|个百分点)',suffix):continue
   clause=re.split(r'[,，。；;]',text[:m.start()])[-1]
   amount=decimal_token(m.group())
   if any(x in clause for x in ('调整后','重述后','调整值','调整基期')) and amount!=Decimal(p['adjusted_base_CNY']):continue
   if any(x in clause for x in ('调整前','原值','原基期')) and amount!=Decimal(p['original_base_CNY']):continue
   if any(x in clause for x in ('本期','当期','当前')) and amount!=Decimal(p['selected_current_CNY']):continue
   if ('营业收入' in clause or '归母' in clause) and p['field']=='NetProfit':continue
   if '合并净利润' in clause and p['field']=='NPParentCompanyOwners':continue
   if re.match(r'\s*(?:CNY|人民币元|元)(?![A-Za-z])',suffix) or ('单位CNY' in clause or '单位为CNY' in clause):spans.append({'start':m.start(),'end':m.end(),'role':'registered_basis_CNY_amount','source_text':m.group()})
 else:raise ValueError('unknown_record_kind_numeric_role')
 # Chinese quantities are covered by the same approved occurrence spans.
 rejected=[];approved=[]
 for m in occurrences(text):
  roles=[s['role'] for s in spans if s['start']<=m.start() and m.end()<=s['end']]
  item={'start':m.start(),'end':m.end(),'token':m.group(),'roles':roles}
  (approved if roles else rejected).append(item)
 if rejected and not partial:raise ValueError(kind+'_numeric_occurrence_without_registered_role:'+','.join(x['token'] for x in rejected))
 if not partial and kind in ('formula','policy') and BUSINESS_RESULT.search(text):raise ValueError(kind+'_cannot_support_company_numeric_result')
 if not partial and kind=='formula' and any(unit in text for unit in ('CNY','人民币','万元','亿元','美元')):raise ValueError('formula_not_company_amount_source')
 return {'kind':kind,'status':'executed','valid':True,'approved_occurrences':approved,'unapproved_occurrences':rejected,'partial_role_union_only':partial,'source_role_spans':spans,'not_a_semantic_QA_pass':True}
