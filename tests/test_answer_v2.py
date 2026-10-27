import unittest
from fin_analysis.answer_v2 import resolve_answer


class ReferenceContract(unittest.TestCase):
    def setUp(self):
        self.registry = {'B1': {'kind': 'basis', 'company_code': 'SYN001',
            'period': '2022-12-31', 'scope': 'consolidated', 'value': '100', 'unit': 'CNY'},
            'P1': {'kind': 'policy', 'text': 'Synthetic policy'}}

    def test_registered_basis_period_survives_and_output_is_detached(self):
        answer = {'facts': [{'ref': 'B1'}], 'references': [{'ref': 'P1'}]}
        result = resolve_answer(answer, self.registry)
        self.assertEqual(result['facts'][0]['record']['period'], '2022-12-31')
        self.assertEqual(result['semantic_acceptance'], 'not_evaluated')
        result['facts'][0]['record']['period'] = '2099-12-31'
        self.assertEqual(self.registry['B1']['period'], '2022-12-31')

    def test_wrong_period_or_policy_fact_or_unknown_ref_rejected(self):
        for facts in ([{'ref': 'B1', 'period': '2023-12-31'}],
                      [{'ref': 'P1'}], [{'ref': 'UNKNOWN'}], [{'ref': 'B1'}, {'ref': 'B1'}]):
            with self.subTest(facts=facts), self.assertRaises(ValueError):
                resolve_answer({'facts': facts, 'references': []}, self.registry)

    def test_financial_card_not_a_reference_and_malformed_input_rejected(self):
        for answer in ({'facts': [], 'references': [{'ref': 'B1'}]},
                       {'facts': None, 'references': []}, {'facts': []}, []):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                resolve_answer(answer, self.registry)
