import unittest
from fin_analysis import numeric_roles as n
class Roles(unittest.TestCase):
 def test_same_value_wrong_metric(self):
  p={'display_value':'17.50','display_name':'合并净利润同比','period':'2024-12-31','unit_label':'%','metric':'profit_growth','scope':'合并报表','_company_code':'SYN001'}
  n.check('合并净利润同比百分之十七点五','fact',p)
  with self.assertRaises(ValueError):n.check('合并净利润同比17.50%，营业收入同比17.50%','fact',p)
 def test_policy_chinese_money_not_authorized(self):
  p={'policy_name':'企业会计准则解释第16号','effective_date':'2023-01-01'}
  n.check('解释第16号自2023-01-01起执行','policy',p)
  for text in ('公司净利润增加九百九十九元','公司净利润增加玖佰玖拾玖元','公司净利润增加９９９元'):
   with self.assertRaises(ValueError):n.check(text,'policy',p)
