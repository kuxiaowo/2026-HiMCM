"""Archive retired prototype scripts and prevent accidental current overwrites."""
from pathlib import Path
import shutil,re
ROOT=Path(__file__).resolve().parents[2];DST=ROOT/'output/question6/archive/synthetic_20261006/scripts'
def main():
 DST.mkdir(exist_ok=True,parents=True)
 for name in ['build_question6.py','verify_question6.py','build_question6_paper_figures.py','write_question6_chapter.py']:
  p=ROOT/'scripts/modeling'/name;s=p.read_text(encoding='utf8')
  if 'Historical synthetic prototype retired' in s:continue
  shutil.copy2(p,DST/name)
  s=re.sub(r"(if __name__\s*==\s*['\"]__main__['\"]\s*:)([^\n]*)",lambda m:m[1]+"\n    raise SystemExit('Historical synthetic prototype retired; use question6_real scripts. Original retained in output/question6/archive/synthetic_20261006/scripts.')\n    "+m[2].strip(),s)
  p.write_text(s,encoding='utf8')
 for stem in ['fig2_prototype_networks','fig3_adaptation_results']:
  for ext in ['.png','.svg','.tikz']:
   p=ROOT/'output/question6/paper_figures'/(stem+ext)
   if p.exists():
    dst=ROOT/'output/question6/archive/synthetic_20261006/paper_figures'/p.name
    dst.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,dst)
    assert p.resolve().is_relative_to(ROOT) and dst.resolve().is_relative_to(ROOT)
    assert p.read_bytes()==dst.read_bytes();p.unlink()
 print('Retired scripts guarded and old figures archived.')
if __name__=='__main__':main()
