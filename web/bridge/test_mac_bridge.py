import unittest
from mac_bridge import public_state, server_allowed


class PrivacyTests(unittest.TestCase):
    def test_state_omits_content_and_trace_but_keeps_approval_plan(self):
        state = {'root':'/private/home', 'assets':[{'id':'a','project':'p','original':'/private/notes.txt','path':'/private/notes.txt',
                  'plan':{'action':'file','target':'/projects/notes.txt'}, 'run':{'status':'planned','full':[{'secret':'body'}], 'trace':['private content']},
                  'why':['Project hint']}], 'catalog':[{'id':'p','name':'Project','profile':'private data'}],
                 'trashed':[], 'journal':[{'src':'/private/notes.txt'}]}
        result = public_state(state)
        self.assertEqual(result['assets'][0]['name'], 'notes.txt')
        self.assertEqual(result['assets'][0]['project'], 'p')
        self.assertEqual(result['assets'][0]['plan'], state['assets'][0]['plan'])
        self.assertNotIn('/private', str(result))
        self.assertNotIn('private content', str(result))
        self.assertNotIn('body', str(result))


class ServerUrlTests(unittest.TestCase):
    def test_plain_http_requires_explicit_loopback_mode(self):
        self.assertFalse(server_allowed('http://127.0.0.1:8000'))
        self.assertTrue(server_allowed('http://127.0.0.1:8000', True))
        self.assertTrue(server_allowed('http://localhost:8000', True))
        self.assertFalse(server_allowed('http://127.0.0.1.evil.example:8000', True))
        self.assertFalse(server_allowed('http://192.168.1.10:8000', True))
        self.assertFalse(server_allowed('http://localhost:8000/path', True))
        self.assertTrue(server_allowed('https://3.38.192.19'))


if __name__ == '__main__':
    unittest.main()
