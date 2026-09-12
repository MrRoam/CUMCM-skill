"""Structural safety checks: incomplete runs, missing truth and invalid histories."""
import copy
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from build_replay import build, validate


def example():
    explain={'start':1,'end':1,'title':'测量','action':'原地检测C1','feedback':'无信号',
             'why':'日志未记录选择依据','focus':1}
    channel={'j':1,'status':'unknown'}
    return {'case':{'sources':[]},'scene':{},
            'frames':[{'q':[0,0],'time':0,'complete':False,'seen':[],'channels':[channel]},
                      {'q':[0,0],'time':5,'complete':False,'seen':[],'channels':[channel]}],
            'actions':[{'kind':'measure','position':[0,0],'channel':1,'result':'no_signal','bearing':None}],
            'single':[explain],'groups':[explain]}


class ReplayTests(unittest.TestCase):
    def test_incomplete_without_truth_can_render(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'replay.html';r=build(example(),out)
            self.assertFalse(r['complete']);self.assertEqual(r['actions'],1)
            self.assertLess(out.stat().st_size,1_000_000)

    def test_false_completion_rejected(self):
        d=example();d['frames'][-1]['complete']=True
        with self.assertRaises(ValueError):validate(d)

    def test_missing_group_rejected(self):
        d=example();d['groups']=[]
        with self.assertRaises(ValueError):validate(d)

    def test_backward_time_rejected(self):
        d=example();d['frames'][0]['time']=6
        with self.assertRaises(ValueError):validate(d)

    def test_position_mismatch_rejected(self):
        d=example();d['actions'][0]['position']=[1,0]
        with self.assertRaises(ValueError):validate(d)

    def test_log_text_cannot_close_json_script(self):
        d=example();d['single'][0]['why']='</script><script>throw Error(1)</script>'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'replay.html';build(d,p)
            self.assertNotIn('</script><script>throw',p.read_text(encoding='utf-8'))

    def test_standalone_embeds_styles_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'replay.html';build(example(),p,standalone=True)
            text=p.read_text(encoding='utf-8')
            self.assertTrue(text.startswith('<!doctype html>'))
            self.assertIn('--viz-series-1:',text)
            self.assertNotIn('<script src=',text)

    def test_raw_q3_without_external_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'run';folder.mkdir()
            row={'step':1,'kind':'measure','position':[0,0],'channel':1,'reason':'example',
                 'response':{'accepted':True,'measure_result':'no_signal','virtual_time_s':5}}
            (folder/'actions.jsonl').write_text(json.dumps(row),encoding='utf-8')
            output=Path(tmp)/'data.json'
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('adapt_q3.py')),
                                   '--run',str(folder),'--output',str(output)],
                                  cwd=tmp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(data['frames'][-1]['time'],5)
            self.assertFalse(data['frames'][-1]['complete'])
            self.assertEqual(data['case']['sources'],[])


if __name__=='__main__':unittest.main()
