import subprocess,shutil,unittest
from pathlib import Path
class WebSyntax(unittest.TestCase):
 @unittest.skipUnless(shutil.which('node'),'Node optional syntax check')
 def test_all_javascript_parses(self):
  for path in (Path(__file__).resolve().parents[1]/'customchat/web').glob('*.js'):
   with self.subTest(file=path.name):
    p=subprocess.run(['node','--check',str(path)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_background_marker_updates_on_input_and_upload(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/settings.js').read_text();self.assertIn('marker.hidden=!!link.value.trim()',s);self.assertIn('setv(f,data);syncMarker()',s);self.assertIn('if(!link.value.trim())file.value=""',s)

 def test_optional_workspace_marker_tracks_input(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/configstate.js').read_text();self.assertIn("if(typeof value==='string'||value===null)",s);self.assertIn('marker.hidden=!!input.value.trim()',s);self.assertIn("input.addEventListener('input',sync)",s)

 def test_fallback_is_typed_not_null_text(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/configstate.js').read_text();self.assertIn("path.join('.')==='provider.fallback'",s);self.assertIn('read?read():',s);self.assertIn('if(!enabled.checked)return null',s);self.assertNotIn("input.placeholder='(not filled)'",s)

 def test_extension_text_preserves_multiline_and_numbers_are_not_empty_zero(self):
  s=(Path(__file__).resolve().parents[1]/'customchat/web/configstate.js').read_text();self.assertIn("input=el(typeof value==='string'?'textarea':'input')",s);self.assertIn("number(input,path.join('.'))",s);self.assertIn("if(!input.value.trim()||!Number.isFinite(Number(input.value)))",s)
