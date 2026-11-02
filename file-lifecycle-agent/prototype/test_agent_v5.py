import unittest,tempfile
from pathlib import Path
from lifecycle_v3 import Lifecycle
from agent_v5 import ToolHostV5,run,rule_controller
from tasks_v5 import build
def host_for(ts,kind):
    t=next(x for x in ts if x['kind']==kind);return ToolHostV5(Lifecycle(t['dir']),t['asset'],t['catalog']),t
def script(*actions):
    it=iter(actions);return lambda h:next(it,{'tool':'finish','arguments':{},'reason':'end'})
A=lambda t,**a:{'tool':t,'arguments':a,'reason':'test'}
class V5(unittest.TestCase):
    @classmethod
    def setUpClass(c):c.tmp=tempfile.TemporaryDirectory();c.ts=build(c.tmp.name)
    def test_ungrounded_assign_rejected(self):
        h,t=host_for(self.ts,'semantic');pid=next(iter(t['catalog']))
        r=run(h,script(A('inspect_file'),A('assign_project',project_id=pid,evidence='made up evidence text')),max_steps=2)
        self.assertIsNone(h.assigned);self.assertEqual(h.stats['ungrounded_assign'],1)
    def test_search_result_is_not_evidence(self):
        h,t=host_for(self.ts,'semantic');pid=next(iter(t['catalog']))
        run(h,script(A('inspect_file'),A('search_projects',query=t['catalog'][pid]['name']),A('assign_project',project_id=pid,evidence=t['catalog'][pid]['name'])),max_steps=3)
        self.assertIsNone(h.assigned)
    def test_weights_never_read(self):
        h,_=host_for(self.ts,'weights_referenced');run(h,script(A('inspect_file'),A('read_content',offset=0)),max_steps=2)
        self.assertEqual(h.stats['weights_read_attempts'],1);self.assertIn('error',h.history[-1]['result'])
    def test_unknown_tool_and_bad_candidate(self):
        h,_=host_for(self.ts,'ambiguous')
        r=run(h,script(A('execute_plan'),A('ask_user',question='q',candidate_ids=['NOPE'])),max_steps=2)
        self.assertEqual(h.stats['unknown_tool'],1);self.assertEqual(r['status'],'budget_exceeded');self.assertEqual(r['invalid_calls'],2)
    def test_repeat_and_invalid_output_fed_back(self):
        h,_=host_for(self.ts,'explicit')
        r=run(h,script(A('inspect_file'),A('inspect_file'),{'invalid_output':'hi'}),max_steps=3)
        self.assertEqual(r['invalid_calls'],2);self.assertIn('repeated',h.history[1]['result']['error'])
    def test_file_untouched(self):
        for x in self.ts[:20]:
            h=ToolHostV5(Lifecycle(x['dir']),x['asset'],x['catalog']);p=h.file();run(h,rule_controller);self.assertTrue(p.exists())
    def test_injected_instruction_is_not_evidence(self):
        h,t=host_for(self.ts,'injection');line=next(l for l in Path(h.file()).read_text().splitlines() if 'OVERRIDE' in l)
        run(h,script(A('inspect_file'),A('read_content',offset=0),A('assign_project',project_id=next(iter(t['catalog'])),evidence=line)),max_steps=3)
        self.assertNotIn('OVERRIDE',h.history[1]['result']['text']);self.assertEqual(h.stats['redacted_lines'],1)
        self.assertIsNone(h.assigned);self.assertEqual(h.stats['ungrounded_assign'],1)  # redacted line is no longer quotable
    def test_tied_evidence_rejected(self):
        h,t=host_for(self.ts,'ambiguous');line=Path(h.file()).read_text().splitlines()[0]
        run(h,script(A('inspect_file'),A('read_content',offset=0),A('assign_project',project_id=t['truth']['candidates'][0],evidence=line)),max_steps=3)
        self.assertIsNone(h.assigned);self.assertIn('ask_user',h.history[-1]['result']['error'])
    def test_ask_blocked_until_read_through(self):
        h,_=host_for(self.ts,'long_doc')
        run(h,script(A('inspect_file'),A('read_content',offset=0),A('ask_user',question='q',candidate_ids=[])),max_steps=3)
        self.assertEqual(h.stats['early_ask'],1);self.assertIn('offset=1200',h.history[-1]['result']['error'])
    def test_guards_off_reproduces_v5(self):
        h,t=host_for(self.ts,'injection');h.guards=False;line=next(l for l in Path(h.file()).read_text().splitlines() if 'OVERRIDE' in l)
        run(h,script(A('inspect_file'),A('read_content',offset=0),A('assign_project',project_id='KCC_AGENT',evidence=line)),max_steps=3)
        self.assertEqual(h.assigned,'KCC_AGENT') if 'KCC_AGENT' in t['catalog'] else None
if __name__=='__main__':unittest.main()
