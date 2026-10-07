"""Render current revision PDFs and record measurements, without claiming visual approval.

Run with the bundled document Python (pdfplumber, Pillow). All files stay in-project.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / 'output/pdf/skill_checked_20261007'
OUT = ROOT / 'tmp/pdfs/skill_checked_20261007'
DOCUMENTS = ['full_paper', 'full_paper_zh_explained', 'question1_protection_definition',
             'question2_framework', 'question3_framework', 'question4_sensitivity',
             'question5_evaluation', 'question6_adaptation']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--documents', nargs='+', choices=DOCUMENTS, default=DOCUMENTS)
    parser.add_argument('--pdf-directory', default='output/pdf/skill_checked_20261007')
    parser.add_argument('--render-directory', default='tmp/pdfs/skill_checked_20261007')
    args = parser.parse_args()
    global PDF_DIR, OUT
    PDF_DIR = ROOT / args.pdf_directory
    OUT = ROOT / args.render_directory
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / 'render_measurements.json'
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {'documents': {}}
    for name in args.documents:
        pdf = PDF_DIR / (name + '.pdf')
        folder = OUT / name
        folder.mkdir(parents=True, exist_ok=True)
        pages = []
        texts = []
        with pdfplumber.open(pdf) as document:
            for number, page in enumerate(document.pages, 1):
                text = page.extract_text(layout=False) or ''
                texts.append(text)
                assert not re.search('[\ufffd\u25a1\u25a0]', text), (name, number, 'Missing-glyph marker')
                assert '??' not in text, (name, number, 'Unresolved reference')
                visible = [c for c in page.chars if c['text'].strip()]
                outside = [c['text'] for c in visible if c['x0'] < -0.5 or c['x1'] > page.width + .5
                           or c['top'] < -.5 or c['bottom'] > page.height + .5]
                assert not outside, (name, number, outside)
                body = [c for c in visible if 40 < c['top'] < page.height - 42]
                bottom = max((c['bottom'] for c in body), default=0)
                pages.append({'page': number, 'characters': len(visible), 'body_text_bottom_bp': round(bottom, 2),
                              'text_bottom_gap_mm': round((page.height - 42.52 - bottom) * 25.4 / 72, 2),
                              'first_lines': text.splitlines()[:5], 'last_lines': text.splitlines()[-3:],
                              'caption_lines': [line for line in text.splitlines()
                                                if re.match(r'(?:Figure|Table)\s+\d+:|[图表]\s*\d', line)]})
        (folder / 'text.txt').write_text('\n\f\n'.join(texts), encoding='utf-8')
        subprocess.run(['D:/texlive/2026/bin/windows/pdftoppm.exe', '-r', '300', '-png', str(pdf), str(folder/'page')],
                       check=True, capture_output=True)
        files = sorted(folder.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[1]))
        files = [p for p in files if int(p.stem.split('-')[1]) <= len(pages)]
        assert len(files) == len(pages)
        for start in range(0, len(files), 4):
            contact = Image.new('RGB', (1900, 2770), '#dddddd')
            draw = ImageDraw.Draw(contact)
            for j, file in enumerate(files[start:start+4]):
                with Image.open(file) as original:
                    picture = original.convert('RGB')
                    picture.thumbnail((925, 1320))
                    x = (j % 2) * 950 + (950 - picture.width) // 2
                    y = (j // 2) * 1385 + 40
                    contact.paste(picture, (x, y))
                    draw.text(((j % 2)*950+15, (j//2)*1385+10), f'{name}: {start+j+1}', fill='black')
            contact.save(folder / f'contact-{start//4+1:02}.png')
        item = {'pdf': pdf.relative_to(ROOT).as_posix(), 'pdf_sha256': sha(pdf), 'page_count': len(pages),
                'render_dpi': 300, 'render_folder': folder.relative_to(ROOT).as_posix(),
                'all_pages_rendered': True, 'pages': pages, 'visual_review': 'pending'}
        report['documents'][name] = item
        report.update(generated_at_utc=datetime.now(timezone.utc).isoformat(), status='rendered_visual_review_pending')
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'document': name, 'pages': len(pages), 'rendered_at_dpi': 300}), flush=True)


if __name__ == '__main__':
    main()
