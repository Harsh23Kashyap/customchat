import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from customchat import schema, pdfread
from customchat.connectors.local_files import LocalFiles

class RetrievalPlus(unittest.TestCase):
    def test_heading_anchor(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'guide.md').write_text('# Main\nInfo.\n\n## Apples\nApple facts.')
            conn=LocalFiles({'id':'docs','label':'Docs','path':'.'},folder)
            e=conn.search('apple')[0];self.assertEqual(e['section'],'Apples');self.assertIsNone(e['page'])
    def test_default_never_loads_model(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'guide.txt').write_text('Apple food.')
            conn=LocalFiles({'id':'docs','label':'Docs','path':'.'},folder)
            with patch.object(conn,'_model',side_effect=AssertionError):self.assertTrue(conn.search('apple'))
    def test_hybrid_and_rerank_injected(self):
        class Encoder:
            def encode(self, texts, **kwargs):return [[1.,0.] if 'car' in t or 'vehicle' in t else [0.,1.] for t in texts]
        class Reranker:
            def predict(self,pairs):return [1. if 'car' in p[1] else .1 for p in pairs]
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'car.txt').write_text('The car has four wheels.');Path(folder,'fruit.txt').write_text('Apple food.')
            conn=LocalFiles({'id':'docs','label':'Docs','path':'.','semantic_model':folder,'rerank_model':folder},folder)
            with patch.object(conn,'_model',side_effect=lambda p,r:Reranker() if r else Encoder()):
                e=conn.search('vehicle')[0];self.assertIn('car',e['text']);self.assertEqual(conn._vector_revision,conn.revision)
    def test_model_path_check(self):
        with self.assertRaises(ValueError):LocalFiles._model('remote-name',False)
    def test_ocr_missing_tools(self):
        with patch('shutil.which',return_value=None):
            with self.assertRaises(ValueError):pdfread._ocr_page(b'%PDF',1)
    def test_ocr_command_timeout(self):
        import subprocess
        with patch('shutil.which',return_value='local'),patch('subprocess.run',side_effect=subprocess.TimeoutExpired('test',30)):
            with self.assertRaises(ValueError):pdfread._ocr_page(b'%PDF',1)
    def test_scanned_pdf_real_ocr(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
            import pypdf
        except ImportError:self.skipTest('local document extras not installed')
        import shutil,io
        if not shutil.which('tesseract') or not shutil.which('pdftoppm'):self.skipTest('OCR binaries absent')
        image=Image.new('RGB',(1400,600),'white');draw=ImageDraw.Draw(image)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',42)
        draw.text((60,100),'Apples contain dietary fiber and vitamins.',font=font,fill='black')
        buf=io.BytesIO();image.save(buf,format='PDF');data=buf.getvalue()
        result=pdfread.pages(data,ocr=True);self.assertEqual(result[0]['page'],1);self.assertTrue(result[0]['ocr']);self.assertIn('Apples',result[0]['text'])
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'scan.pdf').write_bytes(data)
            conn=LocalFiles({'id':'docs','label':'Docs','path':'.','ocr':True},folder)
            e=conn.search('apples')[0];self.assertEqual(e['page'],1);self.assertTrue(e['ocr'])
    def test_pdf_page_limit(self):
        try:from pypdf import PdfWriter
        except ImportError:self.skipTest('document extra absent')
        import io
        writer=PdfWriter();writer.add_blank_page(100,100);buf=io.BytesIO();writer.write(buf)
        with self.assertRaises(ValueError):pdfread.pages(buf.getvalue(),max_pages=0)
if __name__=='__main__':unittest.main()
