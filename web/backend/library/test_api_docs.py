from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class ApiDocumentationTests(SimpleTestCase):
    def test_all_api_operations_have_menu_and_description(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        expected = {
            'health': {'get'}, 'onboarding': {'get', 'post'}, 'auth/session': {'get'}, 'auth/login': {'post'},
            'auth/logout': {'post'}, 'auth/signup': {'post'}, 'agent/status': {'get'}, 'agent/commands': {'post'},
            'agent/bridge/poll': {'post'}, 'agent/bridge/result': {'post'},
            'local/unlock': {'post'}, 'local/setup': {'get', 'post'},
            'auth/config': {'get'}, 'auth/apple/start': {'get'}, 'auth/apple/callback': {'post'},
            'agent/pairing': {'post'}, 'agent/pairing/consume': {'post'},
            'agent/pairing/disconnect': {'post'}, 'local/cloud/connect': {'post'},
            'local/cloud/disconnect': {'post'},
            'devices': {'get', 'post'}, 'folders': {'get', 'post'},
            'files': {'get', 'post'}, 'reviews': {'get', 'post'},
        }
        for path, methods in expected.items():
            self.assertTrue(methods <= schema['paths'][f'/api/v1/{path}/'].keys())
        for path, operations in schema['paths'].items():
            if not path.startswith('/api/v1/'):
                continue
            for method, operation in operations.items():
                with self.subTest(path=path, method=method):
                    self.assertTrue(operation['tags'])
                    self.assertTrue(operation['summary'])
                    self.assertTrue(operation['description'])
        command = schema['paths']['/api/v1/agent/commands/']['post']
        self.assertIn('201', command['responses'])
        self.assertEqual(command['requestBody']['content']['application/json']['schema']['required'], ['link_id', 'action'])
