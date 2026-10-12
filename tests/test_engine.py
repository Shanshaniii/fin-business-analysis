import unittest,copy
from pathlib import Path
from fin_analysis.engine import load,calculate,run
DATA=Path(__file__).resolve().parents[1]/'data/synthetic.json'
class Engine(unittest.TestCase):
 def test_seven_metrics_and_missing_base(self):
  result=run(DATA);self.assertEqual(len(result['records']),2)
  current=result['records'][1];self.assertEqual(len(current['metrics']),7);self.assertEqual(current['metrics']['revenue_growth']['exact_decimal'],'10.0');self.assertEqual(current['metrics']['profit_growth']['display_value'],'20.00');self.assertIsNone(result['records'][0]['metrics']['profit_growth']['exact_decimal'])
 def test_real_data_does_not_inherit_synthetic_comparability(self):
  data,records=load(DATA);data['synthetic']=False;out=calculate(data,records,list(records.values())[1]);self.assertEqual(out['metrics']['profit_growth']['status'],'accounting_basis_unverified')
 def test_wrong_scope_join_rejected(self):
  data,records=load(DATA);list(records.values())[0]['scope']='parent';out=calculate(data,records,list(records.values())[1]);self.assertEqual(out['metrics']['profit_growth']['status'],'incompatible_entity_scope_currency')
 def test_zero_denominator_and_null_cause(self):
  data,records=load(DATA);row=list(records.values())[1];row['fields']['NetProfit']='0';out=calculate(data,records,row);self.assertEqual(out['metrics']['cash_profit_ratio']['status'],'zero_denominator');self.assertIsNone(out['risk_conclusion']);self.assertEqual(out['cause_status'],'not_established')

 def test_negative_profit_interpretation_suspended(self):
  data,records=load(DATA);row=list(records.values())[1];row['fields']['NetProfit']='-10';out=calculate(data,records,row);self.assertEqual(out['metrics']['cash_profit_ratio']['interpretation'],'suspended_nonpositive_profit')
