import unittest
from copy import deepcopy
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

    def test_optional_required_refs_keep_default_interface_compatible(self):
        answer={'facts': [{'ref': 'B1'}], 'references': []}
        expected=resolve_answer(answer, self.registry)
        self.assertEqual(expected,resolve_answer(answer,self.registry,required_tool_refs=[]))
        self.assertEqual(expected,resolve_answer(answer,self.registry,required_tool_refs=['B1']))

    def test_missing_tool_citation_is_rejected_without_filling_answer(self):
        answer={'facts': [], 'references': [{'ref': 'P1'}]}
        before=deepcopy(answer)
        with self.assertRaisesRegex(ValueError,'required_tool_result_not_cited:B1'):
            resolve_answer(answer,self.registry,required_tool_refs=['B1'])
        self.assertEqual(answer,before)

    def test_requirements_must_resolve_to_trusted_financial_records(self):
        for required in ('B1', ['UNKNOWN'], ['P1'], ['B1','B1'], [None]):
            with self.subTest(required=required),self.assertRaises(ValueError):
                resolve_answer({'facts':[{'ref':'B1'}],'references':[]},self.registry,
                               required_tool_refs=required)
        with self.assertRaises(ValueError):
            resolve_answer({'facts':[{'ref':'B1'}],'references':[]},
                           {**self.registry,'BAD':[]},required_tool_refs=['BAD'])
