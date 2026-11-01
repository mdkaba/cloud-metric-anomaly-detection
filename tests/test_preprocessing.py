import sys
from pathlib import Path
import unittest
import csv
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prepare_data import make_features

class CausalityTests(unittest.TestCase):
    def setUp(self):
        self.stamps = [datetime(2020,1,1)+timedelta(minutes=5*i) for i in range(30)]
        self.values = list(range(30))

    def test_current_and_future_values_cannot_change_predictors(self):
        baseline = make_features(self.stamps,self.values,300,[1,2],[3])
        changed = self.values[:]
        changed[15:] = [999]*15
        result = make_features(self.stamps,changed,300,[1,2],[3])
        for before,after in zip(baseline,result):
            if before['timestamp'] <= str(self.stamps[15]):
                self.assertEqual({k:v for k,v in before.items() if k!='target'},
                                 {k:v for k,v in after.items() if k!='target'})

    def test_gap_requires_new_complete_history(self):
        stamps = self.stamps[:10]+[t+timedelta(minutes=5) for t in self.stamps[10:]]
        result = make_features(stamps,self.values,300,[1,2],[3])
        present = {r['timestamp'] for r in result}
        for i in (10,11,12):
            self.assertNotIn(str(stamps[i]),present)
        self.assertIn(str(stamps[13]),present)

    def test_missing_value_is_never_imputed_from_future(self):
        values = self.values[:]
        values[10] = float('nan')
        result = make_features(self.stamps,values,300,[1,2],[3])
        present = {r['timestamp'] for r in result}
        for i in (10,11,12,13):
            self.assertNotIn(str(self.stamps[i]),present)

class PreparedDataTests(unittest.TestCase):
    def test_all_series_have_disjoint_ordered_splits_without_labels(self):
        root = Path(__file__).resolve().parents[1] / 'data/processed'
        folders = sorted(root.glob('*'))
        self.assertEqual(len(folders),17, 'Run the download and preprocessing first')
        for folder in folders:
            previous_end = None
            for split in ('train','development','test'):
                with (folder / f'{split}.csv').open(newline='') as stream:
                    rows = list(csv.DictReader(stream))
                self.assertTrue(rows)
                stamps = [r['timestamp'] for r in rows]
                self.assertEqual(stamps,sorted(set(stamps)))
                if previous_end is not None:
                    self.assertLess(previous_end,stamps[0])
                previous_end = stamps[-1]
                self.assertEqual(set(rows[0]), {'timestamp','target','lag_1','lag_2',
                    'lag_3','lag_6','lag_12','mean_6','std_6','mean_12','std_12'})

if __name__ == '__main__':
    unittest.main()
