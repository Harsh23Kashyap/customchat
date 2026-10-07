import os, unittest
from unittest.mock import patch
from customchat.terminal import styled
class Stream:
    def __init__(self,tty):self.tty=tty
    def isatty(self):return self.tty
class Terminal(unittest.TestCase):
    def test_redirect_plain(self):self.assertEqual(styled('Hello',stream=Stream(False)),'Hello')
    def test_no_color(self):
        with patch.dict(os.environ,{'NO_COLOR':'1'}):self.assertEqual(styled('Hello',stream=Stream(True)),'Hello')
    def test_tty(self):
        with patch.dict(os.environ,{'TERM':'xterm'},clear=True):self.assertIn('\033[36m',styled('Hello',stream=Stream(True)))
    def test_dumb(self):
        with patch.dict(os.environ,{'TERM':'dumb'},clear=True):self.assertEqual(styled('Hello',stream=Stream(True)),'Hello')
if __name__=='__main__':unittest.main()
