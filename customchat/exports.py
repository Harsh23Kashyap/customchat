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


def snapshot(e):
    return " · ".join(str(x) for x in [e.get("document"), "page "+str(e["page"]) if e.get("page") else e.get("section"), "version "+str(e["version"]) if e.get("version") else "", "OCR" if e.get("ocr") else ""] if x)


def answer_markdown(app,turn):
    out=["# "+app.get("title","Chat"),app.get("tagline",""),"", "## Question",turn['question'],"", "## Answer",turn['answer'],"", "## Source snapshot"]
    for i,e in enumerate(turn['evidence'],1):
        out += ["[%d] %s" % (e.get('n',i),e['title']),e.get('url',''),snapshot(e),""]
    out += ["Source versions are snapshots at answer time. They are not a guarantee the linked document is unchanged."]
    return "\n".join(out)


def pdf_bytes(title, turn, accent="#173f35", tagline=""):
    # Standard PDF fonts cover Latin-1. Never silently substitute missing characters.
    lines=[title,tagline,"", "QUESTION",turn['question'],"", "ANSWER"]
    lines += turn['answer'].split("\n")
    lines += ["", "SOURCE SNAPSHOT"]
    for i,e in enumerate(turn['evidence'],1):
        lines += ["[%d] %s" % (e.get('n',i),e['title']),e.get('url',''),snapshot(e).replace(" · "," | ")]
    lines += ["", "Versions are snapshots at answer time; linked sources may change."]
    try:"\n".join(lines).encode('latin-1')
    except UnicodeEncodeError:raise ValueError("PDF font cannot represent this text. Download Markdown for full Unicode.") from None
    wrapped=[]
    for line in lines:wrapped += textwrap.wrap(line,88,replace_whitespace=False) or [""]
    pages=[wrapped[i:i+48] for i in range(0,len(wrapped),48)]
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',accent):accent='#173f35'
    rgb=' '.join('%.3f'%(int(accent[i:i+2],16)/255) for i in (1,3,5))
    objs=["<< /Type /Catalog /Pages 2 0 R >>", "", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    ids=[]
    for n,rows in enumerate(pages,1):
        page_id=len(objs)+1;content_id=page_id+1;ids.append(page_id)
        stream=rgb+" rg 50 787 495 2 re f\n0.09 0.14 0.12 rg\nBT /F1 10 Tf 50 770 Td 14 TL\n"+"\n".join("(%s) Tj T*"%_pdf_escape(l) for l in rows)+"\nET\nBT /F1 9 Tf 50 40 Td ("+_pdf_escape(title[:60])+" | "+str(n)+" / "+str(len(pages))+") Tj ET"
        objs.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents %d 0 R /Resources << /Font << /F1 3 0 R >> >> >>"%content_id)
        objs.append("<< /Length %d >>\nstream\n%s\nendstream"%(len(stream.encode('latin-1')),stream))
    objs[1]="<< /Type /Pages /Kids ["+' '.join('%d 0 R'%i for i in ids)+"] /Count %d >>"%len(ids)
    out,offs=b"%PDF-1.4\n",[]
    for i,o in enumerate(objs,1):
        offs.append(len(out));out+=("%d 0 obj\n%s\nendobj\n"%(i,o)).encode('latin-1')
    x=len(out);out+=("xref\n0 %d\n0000000000 65535 f \n"%(len(objs)+1)).encode()
    for o in offs:out+=("%010d 00000 n \n"%o).encode()
    out+=("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"%(len(objs)+1,x)).encode()
    return out


def chat_markdown(title, turns):
    out = ["# " + title, ""]
    for t in turns:
        out += ["**Q:** " + t["question"], "", t["answer"], ""]
        for i, e in enumerate(t["evidence"], 1):
            out.append("%d. %s%s" % (i, e["title"], " <%s>" % e["url"] if e["url"] else ""))
        out.append("")
    return "\n".join(out)
