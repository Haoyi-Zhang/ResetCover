"""Benign row/projection and zero-action boundary regressions."""
import json
from copy import deepcopy
from pathlib import Path
import sys
import unittest

A=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(A/'src'),str(A/'tests')]
from checker import InvalidCertificate, check_rank, replay
from generators import one_shot
from oracles import unary_depth, unary_machines
from solver import solve


class ReplayBinding(unittest.TestCase):
    def setUp(self):
        self.f=one_shot('owned-binding',[[0],[1]])
        self.r=solve(self.f,0,seconds=5)
        check_rank(self.f,self.r['certificate'])

    def test_singletons_have_zero_prefix_depth(self):
        for machine in unary_machines():
            f={'actions':['tick'],'observations':[0,1],'machines':[machine]}
            r=solve(f,0,seconds=5)
            self.assertEqual(unary_depth(f['machines']),0)
            self.assertEqual(check_rank(f,r['certificate'])['depth'],0)
            self.assertEqual(replay(f,r['certificate'],r['strategy'])['worst_depth'],0)
        with self.assertRaises(ValueError):
            unary_depth([])

    def test_strategy_root_kind(self):
        for alias in (False,0.0):
            strategy=deepcopy(self.r['strategy'])
            strategy['root']=alias
            with self.assertRaisesRegex(InvalidCertificate,'DAG root'):
                replay(self.f,self.r['certificate'],strategy)

    def renamed_leaves(self, replacement):
        strategy=deepcopy(self.r['strategy'])
        for row in strategy['nodes']:
            row['node']=replacement.get(row['node'],row['node'])
            for edge in row.get('edges',[]):
                edge[1]=replacement.get(edge[1],edge[1])
        return strategy

    def test_nonexistent_certificate_row(self):
        with self.assertRaisesRegex(InvalidCertificate,'row index'):
            replay(self.f,self.r['certificate'],self.renamed_leaves({1:999}))

    def test_in_range_wrong_row_projection(self):
        with self.assertRaisesRegex(InvalidCertificate,'row/history binding'):
            replay(self.f,self.r['certificate'],self.renamed_leaves({1:2,2:1}))

    def test_consistent_certificate_row_reordering(self):
        c=deepcopy(self.r['certificate'])
        n=len(c['rows'])
        c['rows'].reverse(); c['root']=n-1-c['root']
        strategy=self.renamed_leaves({i:n-1-i for i in range(n)})
        strategy['root']=c['root']
        check_rank(self.f,c)
        self.assertEqual(replay(self.f,c,strategy)['worst_depth'],1)

    def test_all_retained_main_packets_unchanged(self):
        count=positive=0
        for item in json.loads((A/'inputs/catalog.json').read_text()):
            f=json.loads((A/'inputs'/item['file']).read_text())
            packet=json.loads((A/'results/certificates'/(item['name']+'.json')).read_text())
            self.assertEqual(packet['game']['resets'],item['resets'])
            self.assertEqual(set(packet['game']['support']),set(range(len(f['machines']))))
            result=check_rank(f,packet['game'])
            if result['status']=='identified':
                self.assertEqual(replay(f,packet['game'],packet['strategy'])['worst_depth'],result['depth'])
                positive+=1
            count+=1
        self.assertEqual((count,positive),(48,24))


if __name__=='__main__':
    unittest.main()
