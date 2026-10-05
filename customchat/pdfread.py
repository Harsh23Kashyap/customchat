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
