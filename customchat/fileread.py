"""Local, bounded extraction. Uploaded bytes never go to a vision service."""
import shutil, subprocess, tempfile, zipfile, io
from pathlib import Path
from xml.etree import ElementTree as ET
from . import pdfread


def extract(name, data):
    if not data or len(data) > 8_000_000:
        raise ValueError('File must be nonempty and at most 8 MB')
    ext = Path(name).suffix.lower()
    if ext == '.pdf': return pdfread.extract(data)
    if ext in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff'):
        if not shutil.which('tesseract'):
            raise ValueError('Image text recognition needs Tesseract installed on this computer. No image was indexed.')
        with tempfile.TemporaryDirectory(prefix='cc-image-') as folder:
            image = Path(folder) / ('image' + ext); image.write_bytes(data)
            try: result = subprocess.run(['tesseract', str(image), 'stdout'], capture_output=True, timeout=30)
            except subprocess.TimeoutExpired: raise ValueError('Image text recognition timed out') from None
            if result.returncode: raise ValueError('That image could not be read')
            text = result.stdout.decode('utf-8', errors='replace').strip()
            if not text: raise ValueError('No readable text in this image. Photos and diagrams need a vision model, which is not enabled.')
            return '[Local image OCR. May contain recognition errors.]\n' + text[:149900]
    if ext in ('.docx', '.xlsx', '.pptx', '.odt'):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if len(archive.infolist()) > 2000: raise ValueError('Document contains too many files')
                members = [m for m in archive.infolist() if m.filename.endswith('.xml') and (m.filename in ('word/document.xml', 'xl/sharedStrings.xml', 'content.xml') or m.filename.startswith(('ppt/slides/slide', 'xl/worksheets/sheet')))]
                if sum(m.file_size for m in members) > 20_000_000: raise ValueError('Expanded document is too large')
                if ext == '.xlsx':
                    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    shared = []
                    if 'xl/sharedStrings.xml' in archive.namelist():
                        shared = [''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', ns)]
                    rows = []
                    for m in members:
                        if not m.filename.startswith('xl/worksheets/'): continue
                        for row in ET.fromstring(archive.read(m)).findall('.//s:row', ns):
                            cells = []
                            for cell in row.findall('s:c', ns):
                                value = cell.find('s:v', ns)
                                v = value.text or '' if value is not None else ''.join(cell.itertext())
                                if cell.get('t') == 's':
                                    try: v = shared[int(v)]
                                    except (ValueError, IndexError): v = '[Unreadable cell]'
                                cells.append(cell.get('r', '') + ': ' + v)
                            rows.append(' | '.join(cells))
                    text = '\n'.join(rows)
                else:
                    text = '\n'.join(' '.join(t for t in ET.fromstring(archive.read(m)).itertext() if t.strip()) for m in members)
        except (zipfile.BadZipFile, ET.ParseError): raise ValueError('That document could not be read') from None
    elif ext in ('.txt', '.md', '.csv', '.tsv', '.json', '.yaml', '.yml', '.xml', '.html', '.htm', '.log', '.py', '.js', '.css', '.sql'):
        try: text = data.decode('utf-8-sig')
        except UnicodeDecodeError: raise ValueError('Text files must use UTF-8 encoding') from None
        if '\x00' in text: raise ValueError('This looks like a binary file, not readable text')
    else: raise ValueError('Unsupported file type. Use PDF, PNG/JPG/WebP/GIF, DOCX/XLSX/PPTX/ODT or UTF-8 text. Audio, video, archives and executables are not indexed.')
    if not text.strip(): raise ValueError('No readable text in this file')
    if len(text) > 150_000: raise ValueError('Extracted text is over 150,000 characters; split the file')
    return text
