import sys
import unittest
import subprocess
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'serialization_cost'))
from generators import one_shot, thresholds
from policies import macro_plan
from study import assess, cases
from support_baselines import cases as support_cases, minimum, ordered


class CostTests(unittest.TestCase):
    def test_complete_tiny_and_fixed_seed_cost_cohort(self):
        count=0
        for source,support,budget in cases():
            assess(source,support,budget); count+=1
        self.assertEqual(count,258)

    def test_singleton_and_ambiguity_are_not_positive_costs(self):
        source=thresholds(3,'three')
        for mode in ('whole','prefix'):
            self.assertEqual(macro_plan(source,[0],0,mode)['depth'],0)
            self.assertIsNone(macro_plan(source,[0,1,2],0,mode)['depth'])

    def test_declared_code_order_and_standard_prefix(self):
        source=one_shot('five',[[h] for h in range(5)])
        source['observations']=[4,2,0,3,1]
        _,plans,_=assess(source,list(range(5)),0)
        self.assertEqual(plans['whole']['depth'],4)
        self.assertEqual(plans['prefix']['depth'],4)
        self.assertEqual(plans['bit']['depth'],4)

    def test_receipt_cli_accepts_documented_relative_paths(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='owned-p044-verify-') as temporary:
            result=subprocess.run([sys.executable,'-B','-S',str(root/'serialization_cost'/'verify.py'),
                                   '--normal','serialization_cost/results-normal',
                                   '--optimized','serialization_cost/results-optimized',
                                   '--out',str(Path(temporary)/'verified')],
                                  cwd=root,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_same_guarantee_support_duality_complete_cohort(self):
        comparisons=0
        for source in support_cases():
            results={method:minimum(source,method) for method in ('direct','mss_dual','cover')}
            self.assertEqual(len({r['cardinality'] for r in results.values()}),1)
            clauses=results['mss_dual']['dual_clauses']
            for keep in ordered(len(source['machines'])):
                literal=len(keep)>1 and all(len({source['machines'][h]['table'][0][a][0] for h in keep})<len(keep) for a in range(len(source['actions'])))
                dual=all(set(keep)&set(clause) for clause in clauses)
                self.assertEqual(literal,dual)
                comparisons+=1
        self.assertEqual(comparisons,4388)


if __name__=='__main__': unittest.main()
