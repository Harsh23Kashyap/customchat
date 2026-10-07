"""Pull plain text out of a PDF. Uses pypdf when installed; otherwise a small built-in reader
that handles ordinary text PDFs (Flate-compressed streams with Tj/TJ text operators).
Scanned PDFs (images only) have no text to extract and raise a clear error."""
import re, zlib

MAX_BYTES = 8_000_000


def _unescape(s):
    s = re.sub(rb"\\([nrtbf()\\])", lambda m: {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"", b"f": b""}.get(m.group(1), m.group(1)), s)
    return re.sub(rb"\\([0-7]{1,3})", lambda m: bytes([int(m.group(1), 8) & 255]), s)


def _builtin(data):
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except Exception:
            pass
        if b"BT" not in raw:
            continue
        for blk in re.findall(rb"BT(.*?)ET", raw, re.S):
            for arr in re.finditer(rb"\[(.*?)\]\s*TJ|\((.*?)(?<!\\)\)\s*(?:Tj|'|\")", blk, re.S):
                line = []
                if arr.group(1) is not None:
                    parts = re.findall(rb"\(((?:\\.|[^\\)])*)\)|(-?\d+\.?\d*)", arr.group(1))
                    for t, k in parts:
                        if t or not k:
                            line.append(_unescape(t).decode("latin-1"))
                        elif float(k) < -200:
                            line.append(" ")
                else:
                    line.append(_unescape(arr.group(2)).decode("latin-1"))
                if line:
                    out.append("".join(line))
    return "\n".join(out)


def extract(data):
    if not data.startswith(b"%PDF"):
        raise ValueError("That file is not a PDF")
    if len(data) > MAX_BYTES:
        raise ValueError("PDF is over 8 MB")
    text = ""
    try:
        import io
        from pypdf import PdfReader
        text = "\n\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    except ImportError:
        text = _builtin(data)
    except Exception:
        text = _builtin(data)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) < 20:
        raise ValueError("No readable text in this PDF (it may be a scan)")
    return text[:150_000]


def pages(data, ocr=False, max_pages=100):
    """Page-preserving extraction; OCR is explicit and local, never a web upload."""
    if not data.startswith(b"%PDF") or len(data) > MAX_BYTES:
        raise ValueError("PDF must be valid and at most 8 MB")
    try:
        import io
        from pypdf import PdfReader
    except ImportError:
        raise ValueError("Page anchors need pypdf. Install customchat[documents].") from None
    reader = PdfReader(io.BytesIO(data))
    if len(reader.pages) > max_pages:
        raise ValueError("PDF exceeds the 100-page local extraction limit")
    out = []
    for number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if len(text) < 20 and ocr:
            text = _ocr_page(data, number)
        if text: out.append({"page": number, "text": text[:150000], "ocr": len((page.extract_text() or "").strip()) < 20 and ocr})
    if not out: raise ValueError("No readable text. Set ocr: true and install local OCR tools for scans.")
    return out


def _ocr_page(data, number):
    import shutil, subprocess, tempfile
    from pathlib import Path
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise ValueError("OCR needs pdftoppm (Poppler) and Tesseract installed on this computer")
    with tempfile.TemporaryDirectory(prefix="customchat-ocr-") as folder:
        root = Path(folder); source = root / "document.pdf"; source.write_bytes(data)
        try:
            subprocess.run(["pdftoppm", "-f", str(number), "-l", str(number), "-scale-to", "2000", "-singlefile", "-png", str(source), str(root / "page")],
                           check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result = subprocess.run(["tesseract", str(root / "page.png"), "stdout"], check=True, timeout=30,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except (subprocess.SubprocessError, OSError):
            raise ValueError("Local OCR failed or timed out; no text from that page was indexed") from None
        return result.stdout.decode("utf-8", errors="replace").strip()
