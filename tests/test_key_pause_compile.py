import unittest
from unittest.mock import patch
from customchat import generators
from customchat.connectors.open_sources import OpenAlex
from customchat.connectors.web_search import WebSearch


class KeyPauseAndCompileTests(unittest.TestCase):
    def test_ast_valid_python_still_must_compile(self):
        ok, issues = generators.review_code('clean_query', 'return 1\ndef clean_query(query):\n    return query\n')
        self.assertFalse(ok)
        self.assertTrue(any('outside function' in issue for issue in issues), issues)

    def test_templates_compile(self):
        for kind in generators.KINDS:
            code = generators.code_template(kind, 'Test description')
            compile(code, '<test-helper>', 'exec')
            self.assertTrue(generators.review_code(kind, code)[0])

    def test_openalex_without_key_sends_nothing(self):
        with patch('customchat.secrets.saved', return_value=''), patch.dict('os.environ', {}, clear=True), patch('customchat.connectors.open_sources._get') as get:
            self.assertEqual(OpenAlex({'id':'a','label':'A'}).search('q'), [])
            get.assert_not_called()

    def test_web_without_key_sends_nothing(self):
        with patch('customchat.websearch.has_key', return_value=False), patch('customchat.websearch.search') as search:
            self.assertEqual(WebSearch({'id':'web','label':'Web','providers':['tavily','exa']}).search('q'), [])
            search.assert_not_called()

    def test_known_connector_inference_and_safe_templates(self):
        self.assertEqual(generators.infer_search('Use Tavily for research'), 'tavily')
        self.assertEqual(generators.infer_search('', 'tvly-test-fake'), 'tavily')
        self.assertEqual(generators.infer_search('', 'unknown-key'), '')
        self.assertEqual(generators.infer_search('Use Exa or Tavily'), '')
        for pid in ('tavily','exa','firecrawl','parallel'):
            code = generators.known_search_template(pid)
            self.assertTrue(generators.review_code('search', code)[0])
            self.assertNotIn('tvly-test-fake', code)
