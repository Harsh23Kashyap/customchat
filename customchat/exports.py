"""BibTeX and a dependency-free single-page PDF for an answer."""
import re, textwrap


def _k(e, i):
    a = (e["authors"][0].split()[-1] if e["authors"] else "anon")
    return re.sub(r"\W", "", a) + (e["year"] or "nd") + str(i)


def bibtex(evidence):
    out = []
    for i, e in enumerate(evidence, 1):
        f = {"title": e["title"], "author": " and ".join(e["authors"]), "year": e["year"], "journal": e["venue"], "url": e["url"]}
        body = ",\n".join("  %s = {%s}" % (k, re.sub(r"[{}]", "", v)) for k, v in f.items() if v)
        out.append("@article{%s,\n%s\n}" % (_k(e, i), body))
    return "\n\n".join(out) + "\n"


def _pdf_escape(s):
    return s.encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_bytes(title, turn):
    lines = [title, "", "Q: " + turn["question"], ""]
    for para in turn["answer"].split("\n"):
        lines += textwrap.wrap(para, 92) or [""]
    lines += ["", "References"]
    for i, e in enumerate(turn["evidence"], 1):
        lines += textwrap.wrap("[%d] %s. %s %s" % (i, e["title"], e["year"], e["url"]), 92)
    lines = lines[:58]
    stream = "BT /F1 10 Tf 50 800 Td 13 TL\n" + "\n".join("(%s) Tj T*" % _pdf_escape(l) for l in lines) + "\nET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            "<< /Length %d >>\nstream\n%s\nendstream" % (len(stream.encode("latin-1", "replace")), stream),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += ("%d 0 obj\n%s\nendobj\n" % (i, o)).encode("latin-1", "replace")
    x = len(out)
    out += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)).encode()
    for o in offs:
        out += ("%010d 00000 n \n" % o).encode()
    out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, x)).encode()
    return out


def chat_markdown(title, turns):
    out = ["# " + title, ""]
    for t in turns:
        out += ["**Q:** " + t["question"], "", t["answer"], ""]
        for i, e in enumerate(t["evidence"], 1):
            out.append("%d. %s%s" % (i, e["title"], " <%s>" % e["url"] if e["url"] else ""))
        out.append("")
    return "\n".join(out)
