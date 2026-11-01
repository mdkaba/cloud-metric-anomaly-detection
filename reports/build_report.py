"""Format the reviewed Markdown report as a two-page submission PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'output/pdf'
out.mkdir(parents=True, exist_ok=True)
preview = ROOT / 'tmp/pdfs'
preview.mkdir(parents=True, exist_ok=True)
source = (ROOT/'reports/data_collection_and_preprocessing.md').read_text(encoding='utf-8')
source = source.replace('\u2013','-').replace('\u2014','-')
styles = {
 'body': ParagraphStyle('body',fontName='Times-Roman',fontSize=11,leading=12.6,spaceAfter=5),
 'heading': ParagraphStyle('heading',fontName='Helvetica-Bold',fontSize=11,leading=14,spaceBefore=8,spaceAfter=5),
 'title': ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=17,leading=20,spaceAfter=8),
 'meta': ParagraphStyle('meta',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=3),
 'cell': ParagraphStyle('cell',fontName='Helvetica',fontSize=9,leading=11),
 'th': ParagraphStyle('th',fontName='Helvetica-Bold',fontSize=9,leading=11),
}
def inline(text):
    text=escape(text)
    text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`(.*?)`',r'\1',text)
    return text

story=[]
blocks=source.strip().split('\n\n')
for block in blocks:
    if block.startswith('# '):
        story.append(Paragraph(inline(block[2:]),styles['title']))
    elif block.startswith('**Project:**'):
        for line in block.splitlines():
            if line.startswith('**Status:**'):
                continue
            story.append(Paragraph(inline(line.strip()),styles['meta']))
        story.append(Paragraph('Data milestone | November 1, 2026',styles['meta']))
        story.append(Spacer(1,4))
    elif block.startswith('## '):
        if block.startswith('## Chronological'):
            story.append(PageBreak())
        story.append(Paragraph(inline(block[3:]),styles['heading']))
    elif block.startswith('|'):
        rows=[]
        for i,line in enumerate(block.splitlines()):
            if i==1: continue
            rows.append([Paragraph(inline(c.strip()),styles['th' if i==0 else 'cell']) for c in line.strip('|').split('|')])
        widths=[365,145] if len(rows[0])==2 else [95,140,110,165]
        table=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9edf1')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#7c8793')),
            ('LINEBELOW',(0,1),(-1,-1),0.25,colors.HexColor('#d4d9de')),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5),
        ]))
        story.extend([table,Spacer(1,7)])
    else:
        story.append(Paragraph(inline(' '.join(block.splitlines())),styles['body']))

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#c4cbd2'))
    canvas.line(51,39,561,39)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.HexColor('#505a64'))
    canvas.drawString(51,27,'Mamadou Kaba | COEN 6314 | Data Collection and Preprocessing')
    canvas.drawRightString(561,27,str(doc.page))

path=out/'COEN6314_Data_Collection_and_Preprocessing.pdf'
doc=SimpleDocTemplate(str(path),pagesize=letter,leftMargin=51,rightMargin=51,
    topMargin=40,bottomMargin=49,title='Data Collection and Preprocessing',author='Mamadou Kaba')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
reader=PdfReader(path)
print('Pages:',len(reader.pages))
for i,page in enumerate(reader.pages):
    print('Page',i+1,'words:',len(page.extract_text().split()))
pdf=pdfium.PdfDocument(str(path))
for i in range(len(pdf)):
    pdf[i].render(scale=1.5).to_pil().save(preview/f'report-{i+1}.png')
assert len(reader.pages)==2, 'Report must fit exactly two pages'
print(path)
