#!/usr/bin/env python3
"""Make a fresh unsigned development copy; never change the release bundle."""
import argparse,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('destination',type=Path)
p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parents[1]/'bundle')
p.add_argument('--hub',required=True)
a=p.parse_args()
src=a.bundle.resolve(strict=True); out=a.destination.resolve()
if out.exists() or out==Path('/') or src==out or src in out.parents:
 p.error('destination must be a NEW directory outside the source bundle')
shutil.copytree(src,out,symlinks=True)
m=out/'manifest.json'; d=json.loads(m.read_text()); d.get('integrity',{}).pop('signature',None)
m.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
subprocess.run([a.hub,'stamp',str(out)],check=True)
print(f'Unsigned copy ready: {out}; source preserved')
