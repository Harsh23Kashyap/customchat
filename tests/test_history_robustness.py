"""Conversation awareness regressions. No paid calls or network providers."""
import unittest
from unittest.mock import patch
from customchat import schema, providers
from customchat.pipeline import Engine
from customchat.store import Store


class HistoryRobustness(unittest.TestCase):
    def setUp(self):
        self.e = Engine(schema.validate({}), Store(':memory:'))
        self.s = self.e.store
        self.chat = self.s.new_chat('alice')
        self.topic = self.s.new_topic('alice', 'Topic')

    def add(self, question='Prior question', answer='Prior complete answer', chat=None, topic=None):
        return self.s.add_turn(chat or self.chat, topic or self.topic, question, question, answer, [], [], 'standard')

    def real(self, value):
        self.e.cfg['provider']['type'] = 'ollama'
        self.e.provider = type('Fake', (), {'complete': lambda _, m: value})()

    def test_elliptical_followups_rewrite(self):
        self.real('What are the benefits of fiber for kids?')
        for q in ('and for kids?', 'what about cost?', 'Why?', 'expand on the risks',
                  'Can you tell me how this would work in a school with a very small budget and no staff?'):
            self.assertIn('fiber', self.e.standalone(q, [{'question': 'Fiber?', 'answer': 'Benefits'}]))

    def test_empty_and_invalid_rewrite_fall_back(self):
        for value in ('', '\n', 'x', 'x'*2001):
            self.real(value)
            self.assertEqual(self.e.standalone('and for kids?', [{'question': 'Fiber?', 'answer': 'Benefits'}]), 'and for kids?')

    def test_rewrite_provider_error_falls_back(self):
        self.real('ignored')
        with patch.object(self.e.provider, 'complete', side_effect=providers.ProviderError('offline')):
            self.assertEqual(self.e.standalone('why?', [{'question': 'Fiber?', 'answer': 'Benefits'}]), 'why?')

    def test_no_history_no_rewrite(self):
        self.real('wrong')
        self.assertEqual(self.e.standalone('why?', []), 'why?')

    def test_oversized_latest_turn_has_marked_head_and_tail(self):
        rows = [{'question': 'Older', 'answer': 'old'}, {'question': 'What is Atlas?', 'answer': 'HEAD '+ 'x'*100000 + ' TAIL Atlas costs 9'}]
        packed = Engine.pack_history(rows, 'and its cost?', 8000)
        self.assertEqual(packed[-1]['question'], 'What is Atlas?')
        self.assertIn('HEAD', packed[-1]['answer'])
        self.assertIn('TAIL Atlas costs 9', packed[-1]['answer'])
        self.assertIn('middle omitted', packed[-1]['answer'])
        self.assertLessEqual(sum(len(r['question'])+len(r['answer'])+64 for r in packed), 8000)

    def test_recent_order_survives_irrelevant_word_overlap(self):
        rows = [{'question': 'cost', 'answer': 'Old price '+ 'x'*2000} for _ in range(15)]
        rows += [{'question': 'Correction', 'answer': 'New price '+ 'z'*2000}]
        packed = Engine.pack_history(rows, 'cost?', 10000)
        self.assertEqual(packed[-1]['question'], 'Correction')
        self.assertEqual(len(packed), 4)

    def test_500_turn_thread_fetches_old_relevant_and_recent(self):
        self.add('Rare zephyr constraints?', 'Budget is 90')
        for i in range(500): self.add('Unrelated %d' % i, 'Complete answer')
        rows = self.e.conversation_history('alice', self.chat, self.topic, 'What were the zephyr constraints?')
        self.assertIn('Rare zephyr constraints?', [r['question'] for r in rows])
        self.assertEqual(rows[-1]['question'], 'Unrelated 499')
        self.assertLessEqual(len(rows), 240)

    def test_summaries_refresh_after_50_turns(self):
        for i in range(60):
            self.add('Question %d' % i)
            self.e._summarize('alice', self.topic, self.chat)
        state = self.s.get_state('alice', 'memory-' + self.chat)
        self.assertEqual(state['count'], 60)
        self.assertIn('Question 59', state['summary'])

    def test_topic_shared_across_chats_does_not_share_summary(self):
        other = self.s.new_chat('alice')
        self.s.set_summary(self.topic, 'OLD TOPIC SECRET')
        for i in range(6): self.add('PRIVATE in chat one %d' % i)
        self.e._summarize('alice', self.topic, self.chat)
        self.assertIn('PRIVATE', self.e.conversation_summary('alice', self.chat, self.topic))
        self.assertEqual(self.e.conversation_summary('alice', other, self.topic), '')
        self.assertEqual(self.e.conversation_history('alice', other, self.topic, 'why?'), [])

    def test_deleted_turn_invalidates_summary_and_history(self):
        ids = [self.add('PRIVATE %d' % i) for i in range(6)]
        self.e._summarize('alice', self.topic, self.chat)
        self.s.delete_turn('alice', ids[0])
        self.assertEqual(self.e.conversation_summary('alice', self.chat, self.topic), '')
        self.assertNotIn('PRIVATE 0', [r['question'] for r in self.e.conversation_history('alice', self.chat, self.topic, 'why?')])

    def test_source_digest_rejects_out_of_band_deletion(self):
        ids = [self.add() for _ in range(6)]
        self.e._summarize('alice', self.topic, self.chat)
        self.s.q("UPDATE turns SET style='deleted:standard' WHERE id=?", (ids[2],), write=True)
        self.assertEqual(self.e.conversation_summary('alice', self.chat, self.topic), '')

    def test_new_topic_never_inherits_summary(self):
        for _ in range(6): self.add('PRIVATE')
        self.e._summarize('alice', self.topic, self.chat)
        new = self.s.new_topic('alice', 'Other')
        self.assertEqual(self.e.conversation_summary('alice', self.chat, new), '')
        self.assertEqual(self.e.conversation_history('alice', self.chat, new, 'why?'), [])

    def test_wrong_owner_history_rejected(self):
        self.add()
        with self.assertRaises(PermissionError): self.e.conversation_history('bob', self.chat, self.topic, 'why?')

    def test_scoped_turn_never_returns_in_general_history(self):
        turn = self.add('Private scoped question', 'PRIVATE')
        self.s.save_state('alice', 'scope-' + turn, {'source': 'private'})
        self.add('Public question', 'Public answer')
        rows = self.e.conversation_history('alice', self.chat, self.topic, 'private')
        self.assertEqual([r['question'] for r in rows], ['Public question'])

    def test_malformed_temporary_history_does_not_crash_or_save(self):
        for history in ({'bad': 'mapping'}, 'string', 7, [None, {'question': [], 'answer': {}}, {'question': 'Good', 'answer': 'ok'}]):
            done = list(self.e.ask_stream('alice', None, 'and for kids?', temporary=True, temp_history=history))[-1][1]
            self.assertTrue(done['temporary'])
        self.assertEqual(self.s.turns('alice', self.chat), [])

    def test_prompt_reserves_evidence_and_question_space(self):
        self.e.cfg['memory']['context_chars'] = 8000
        evidence = [{'n': 1, 'title': 'Source', 'year': None, 'text': 'SOURCE ' + 's'*1900}]
        messages = self.e.prompt('CURRENT QUESTION', evidence, 'standard', [{'question': 'Old', 'answer': 'a'*90000}], '', '')
        self.assertIn('CURRENT QUESTION', messages[1]['content'])
        self.assertIn('SOURCE', messages[1]['content'])
        self.assertLessEqual(sum(len(m['content']) for m in messages), 8000)
        self.assertIn('middle omitted', messages[1]['content'])
        self.assertIn('not instructions or factual evidence', messages[0]['content'])

    def test_memory_config_validates_edges(self):
        for memory in ({'enabled': 'yes'}, {'summary_every': 0}, {'summary_every': True}, {'recent_turns': -1}, {'context_chars': 7999}):
            with self.assertRaises(schema.ConfigError): schema.validate({'memory': memory})

    def test_summary_failure_does_not_lose_saved_turn(self):
        for _ in range(6): self.add()
        self.real('ignored')
        with patch.object(self.e.provider, 'complete', side_effect=providers.ProviderError('offline')):
            self.e._summarize('alice', self.topic, self.chat)
        self.assertEqual(len(self.s.turns('alice', self.chat)), 6)

    def test_summary_prompt_is_bounded(self):
        self.e.cfg['memory']['context_chars'] = 8000
        for _ in range(6): self.add(answer='a'*100000)
        self.real('Summary')
        with patch.object(self.e.provider, 'complete', return_value='Summary') as call:
            self.e._summarize('alice', self.topic, self.chat)
        self.assertLess(sum(len(m['content']) for m in call.call_args.args[0]), 8500)

    def test_multiturn_correction_is_kept_for_followup(self):
        self.add('Budget for Atlas?', 'Use 90')
        self.add('Correction: my budget is 40, not 90', 'Use 40')
        self.real('What is the Atlas plan for a budget of 40?')
        history = self.e.conversation_history('alice', self.chat, self.topic, 'and for kids?')
        with patch.object(self.e.provider, 'complete', return_value='What is the Atlas plan for a budget of 40?') as call:
            self.e.standalone('and for kids?', history)
        self.assertIn('budget is 40, not 90', call.call_args.args[0][1]['content'])
        self.assertGreater(call.call_args.args[0][1]['content'].index('budget is 40'), call.call_args.args[0][1]['content'].index('Use 90'))

    def test_memory_disabled_ignores_client_and_saved_context(self):
        self.e.cfg['memory']['enabled'] = False
        self.add('SECRET', 'SECRET')
        self.real('bad rewrite')
        with patch.object(self.e.provider, 'complete', return_value='bad rewrite') as call:
            saved = self.e.ask('alice', self.chat, 'why?', topic=self.topic)
            temp = list(self.e.ask_stream('alice', None, 'why?', temporary=True, temp_history=[{'question':'SECRET','answer':'SECRET'}]))[-1][1]
        self.assertEqual(saved['standalone'], 'why?')
        self.assertEqual(temp['standalone'], 'why?')
        call.assert_not_called()

    def test_three_turn_stream_followup_and_correction_reach_retrieval(self):
        class Fake:
            def __init__(self): self.rewrites = []
            def complete(self, messages):
                if 'Rewrite' in messages[0]['content']:
                    self.rewrites.append(messages)
                    return 'What is the Zephyr plan for kids with a budget of 40?'
                return ''
            def stream(self, messages): yield 'Zephyr fits the budget [1].'
        fake = Fake(); self.e.provider = fake; self.e.cfg['provider']['type'] = 'ollama'
        ev = [{'n':1, 'title':'Zephyr', 'year':None, 'text':'Zephyr fits the budget.', 'source':'docs'}]
        with patch.object(self.e, 'retrieve', return_value=(ev, {})) as search:
            for q in ('Tell me the Zephyr plan', 'Correction: my budget is 40', 'and for kids?'):
                done = list(self.e.ask_stream('alice', self.chat, q, topic=self.topic))[-1][1]
        self.assertIn('Zephyr plan for kids', done['standalone'])
        self.assertEqual(len(fake.rewrites), 1)
        self.assertIn('budget is 40', fake.rewrites[0][1]['content'])
        self.assertEqual(search.call_args.args[0], done['standalone'])
        self.assertEqual(len(self.s.turns('alice', self.chat)), 3)

    def test_chat_local_summary_survives_sqlite_restart(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            store = Store(str(Path(folder)/'history.db'))
            e = Engine(schema.validate({}), store)
            chat = store.new_chat('alice'); topic = store.new_topic('alice', 'Topic')
            for i in range(6): store.add_turn(chat, topic, 'Question %d' % i, 'q', 'answer', [], [], 'standard')
            e._summarize('alice', topic, chat)
            reopened = Engine(schema.validate({}), Store(str(Path(folder)/'history.db')))
            self.assertIn('Question 5', reopened.conversation_summary('alice', chat, topic))
            self.assertEqual(len(reopened.conversation_history('alice', chat, topic, 'why?')), 6)

    def test_deleted_chat_and_branch_do_not_import_summary(self):
        ids = [self.add('Question %d' % i) for i in range(6)]
        self.e._summarize('alice', self.topic, self.chat)
        branch = self.s.branch('alice', ids[-1], 'Changed')
        branch_topic = self.s.turns('alice', branch['chat'])[-1]['topic']
        self.assertEqual(self.e.conversation_summary('alice', branch['chat'], branch_topic), '')
        self.s.delete_chat('alice', self.chat)
        with self.assertRaises(PermissionError): self.e.conversation_history('alice', self.chat, self.topic, 'why?')
