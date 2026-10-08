"""Deterministic stage-output checks. Syntax/citation checks do not prove truth."""
import re

def errors(stage, text, evidence_ids=()):
 if not isinstance(text,str):return ['Output must be text']
 t=text.strip();ids=set(evidence_ids)
 if stage=='question_check':return [] if t=='VALID' or re.fullmatch(r'INVALID: [^\n]+',t) else ['Use VALID or INVALID: reason']
 if stage=='faithfulness':return [] if t=='OK' or re.fullmatch(r'UNSUPPORTED: [^\n]+',t) else ['Use OK or UNSUPPORTED: specific claims']
 if stage=='relevance':
  if t=='NONE':return []
  if not re.fullmatch(r'[1-9][0-9]*(?:\s*,\s*[1-9][0-9]*)*',t):return ['Use passage numbers separated by commas, or NONE']
  found=[int(x) for x in re.findall(r'[0-9]+',t)]
  return ['Use only existing, unique passage IDs'] if len(set(found))!=len(found) or not set(found)<=ids else []
 if stage in ('queries','followups'):
  lines=t.splitlines() if t else []
  normalized=[x.strip().casefold() for x in lines]
  return ['Use up to3 distinct plain lines'] if len(lines)>3 or any(not x or len(x)>500 or re.match(r'^\s*(?:[-*]|\d+[.)])\s+',x) for x in lines) or len(set(normalized))!=len(normalized) else []
 if stage=='standalone':return [] if t and len(t)<=2000 and '\n' not in t else ['Use one nonempty question, at most2000 characters']
 if stage=='summary':return [] if len(t)<=600 else ['Summary exceeds600 characters']
 if stage in ('answer','revise'):
  invalid={int(n) for n in re.findall(r'\[([0-9]+)\]',t)}-ids
  if re.search(r'\[(?:0[0-9]+|-?[0-9]+\.[0-9]+|-[0-9]+|[^\x00-\x7f]+)\]',t):return ['Malformed numeric citation']
  return ['Citation IDs do not exist: '+','.join(map(str,sorted(invalid)))] if invalid else []
 raise ValueError('Unknown stage')
