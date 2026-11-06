import unittest
from mac_bridge import public_state


class PrivacyTests(unittest.TestCase):
    def test_state_omits_content_and_trace_but_keeps_approval_plan(self):
        state = {'root':'/private/home', 'assets':[{'id':'a','original':'/private/notes.txt','path':'/private/notes.txt',
                  'plan':{'action':'file','target':'/projects/notes.txt'}, 'run':{'status':'planned','full':[{'secret':'body'}], 'trace':['private content']},
                  'why':['Project hint']}], 'catalog':[{'id':'p','name':'Project','profile':'private data'}],
                 'trashed':[], 'journal':[{'src':'/private/notes.txt'}]}
        result = public_state(state)
        self.assertEqual(result['assets'][0]['name'], 'notes.txt')
        self.assertEqual(result['assets'][0]['plan'], state['assets'][0]['plan'])
        self.assertNotIn('/private', str(result))
        self.assertNotIn('private content', str(result))
        self.assertNotIn('body', str(result))


if __name__ == '__main__':
    unittest.main()
