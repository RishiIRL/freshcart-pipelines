#!/usr/bin/env python3
"""
Generate a professional PDF report from REPORT.md using ReportLab.
"""
import os
import re
import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

# Paths
REPO_DIR = "/home/glitch/Projects/Assignment/freshcart-pipelines"
REPORT_MD = os.path.join(REPO_DIR, "REPORT.md")
OUTPUT_PDF = "/home/glitch/Projects/Assignment/23BCS067_RishiIRL_Pipelines.pdf"
SCREENSHOTS_DIR = "/home/glitch/Projects/Assignment/screenshots"

# Load Markdown
with open(REPORT_MD, "r", encoding="utf-8") as f:
    md_text = f.read()

# Convert Markdown to HTML
html = markdown.markdown(md_text, extensions=["tables", "fenced_code", "codehilite"])

# Parse HTML to ReportLab elements
# We'll do a simple parser that handles:
# - h1, h2, h3
# - p
# - pre (code blocks)
# - code (inline code)
# - ul, li
# - img
# - tables
# - blockquote
# - hr

from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ' '.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class HTMLToReportLab:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='CodeBlock', parent=self.styles['Code'], fontSize=8, leading=10, backColor=colors.HexColor('#f0f0f0'), borderPadding=5, spaceBefore=5, spaceAfter=5))
        self.styles.add(ParagraphStyle(name='InlineCode', parent=self.styles['Code'], fontSize=9, textColor=colors.HexColor('#d63384')))
        self.styles.add(ParagraphStyle(name='H1Center', parent=self.styles['Heading1'], alignment=TA_CENTER, spaceAfter=20))
        self.styles.add(ParagraphStyle(name='H2Styled', parent=self.styles['Heading2'], textColor=colors.HexColor('#1a237e'), spaceBefore=15, spaceAfter=10))
        self.styles.add(ParagraphStyle(name='H3Styled', parent=self.styles['Heading3'], textColor=colors.HexColor('#283593'), spaceBefore=10, spaceAfter=5))
        self.styles.add(ParagraphStyle(name='BlockQuote', parent=self.styles['Normal'], leftIndent=20, textColor=colors.HexColor('#555555'), borderColor=colors.HexColor('#cccccc'), borderWidth=0, spaceBefore=5, spaceAfter=5))
        self.styles.add(ParagraphStyle(name='TableCell', parent=self.styles['Normal'], fontSize=8, leading=10))
        self.styles.add(ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontSize=8, leading=10, textColor=colors.white, fontName='Helvetica-Bold'))
        self.elements = []
        self.current_list = None
        self.in_code = False
        self.code_buffer = []
        self.in_table = False
        self.table_rows = []
        self.table_headers = []

    def parse_html(self, html):
        # Preprocess: split by tags we care about
        # We'll use a regex-based tokenizer for simplicity
        # But better: use HTMLParser
        parser = MyHTMLParser(self)
        parser.feed(html)
        parser.close()

    def add_paragraph(self, text, style='Normal'):
        # Replace inline code
        # text may contain <code>...</code>
        # We'll convert <code> to <font color="...">...</font>
        # But first, unescape HTML entities? Markdown already gave us HTML.
        # Let's handle <code> inline
        # We'll split by <code> and </code>
        parts = re.split(r'(<code>.*?</code>)', text)
        new_text = ""
        for part in parts:
            if part.startswith('<code>') and part.endswith('</code>'):
                code_text = part[6:-7]
                # Escape XML
                code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                new_text += f'<font face="Courier" color="#d63384">{code_text}</font>'
            else:
                new_text += part
        # Replace <br> with <br/>
        new_text = new_text.replace('<br>', '<br/>')
        # Replace <strong> with <b>
        new_text = new_text.replace('<strong>', '<b>').replace('</strong>', '</b>')
        # Replace <em> with <i>
        new_text = new_text.replace('<em>', '<i>').replace('</em>', '</i>')
        # Replace <a href="...">...</a> with <link href="...">...</link>
        new_text = re.sub(r'<a href="([^"]+)">(.*?)</a>', r'<link href="\1" color="blue">\2</link>', new_text)
        # Handle blockquote: if style is BlockQuote, we already have it
        p = Paragraph(new_text, self.styles[style])
        self.elements.append(p)

    def add_code_block(self, code_text):
        # Escape XML
        code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Replace newlines with <br/>
        code_text = code_text.replace('\n', '<br/>')
        # Replace spaces with &nbsp;? No, ReportLab handles spaces in code style
        p = Paragraph(code_text, self.styles['CodeBlock'])
        self.elements.append(p)

    def add_image(self, src, alt=""):
        # Resolve path
        if src.startswith('http'):
            # download? skip for now
            return
        img_path = os.path.join(REPO_DIR, src)
        if not os.path.exists(img_path):
            img_path = os.path.join(SCREENSHOTS_DIR, os.path.basename(src))
        if os.path.exists(img_path):
            img = Image(img_path, width=6*inch, height=4*inch)
            self.elements.append(img)
        else:
            self.elements.append(Paragraph(f"[Image not found: {src}]", self.styles['Normal']))

    def add_table(self, headers, rows):
        # Create table data
        data = []
        # Header
        header_row = [Paragraph(h, self.styles['TableHeader']) for h in headers]
        data.append(header_row)
        # Rows
        for row in rows:
            data_row = [Paragraph(str(cell), self.styles['TableCell']) for cell in row]
            data.append(data_row)
        # Create table
        t = Table(data, colWidths=[2.5*inch]*len(headers))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        self.elements.append(t)
        self.elements.append(Spacer(1, 12))

class MyHTMLParser(HTMLParser):
    def __init__(self, converter):
        super().__init__()
        self.converter = converter
        self.current_tag = None
        self.current_data = ""
        self.list_stack = []
        self.table_stack = []
        self.in_code_block = False
        self.code_text = ""
        self.in_pre = False
        self.pre_text = ""
        self.in_blockquote = False
        self.blockquote_text = ""
        self.in_table = False
        self.in_tr = False
        self.in_th = False
        self.in_td = False
        self.table_headers = []
        self.table_rows = []
        self.current_row = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        if tag == 'h1':
            self.current_data = ""
        elif tag == 'h2':
            self.current_data = ""
        elif tag == 'h3':
            self.current_data = ""
        elif tag == 'p':
            self.current_data = ""
        elif tag == 'pre':
            self.in_pre = True
            self.pre_text = ""
        elif tag == 'code':
            if not self.in_pre:
                # inline code
                self.current_data += "\x00CODE_START\x00"
        elif tag == 'ul':
            self.list_stack.append('ul')
        elif tag == 'ol':
            self.list_stack.append('ol')
        elif tag == 'li':
            self.current_data = ""
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            self.converter.add_image(src, alt)
        elif tag == 'table':
            self.in_table = True
            self.table_headers = []
            self.table_rows = []
        elif tag == 'tr':
            self.in_tr = True
            self.current_row = []
        elif tag == 'th':
            self.in_th = True
            self.current_data = ""
        elif tag == 'td':
            self.in_td = True
            self.current_data = ""
        elif tag == 'blockquote':
            self.in_blockquote = True
            self.blockquote_text = ""

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.converter.add_paragraph(self.current_data, 'H1Center')
        elif tag == 'h2':
            self.converter.add_paragraph(self.current_data, 'H2Styled')
        elif tag == 'h3':
            self.converter.add_paragraph(self.current_data, 'H3Styled')
        elif tag == 'p':
            if self.list_stack:
                # We are inside a list item
                pass
            else:
                self.converter.add_paragraph(self.current_data, 'Normal')
        elif tag == 'pre':
            self.in_pre = False
            self.converter.add_code_block(self.pre_text)
        elif tag == 'code':
            if not self.in_pre:
                self.current_data += "\x00CODE_END\x00"
        elif tag == 'ul':
            if self.list_stack:
                self.list_stack.pop()
        elif tag == 'ol':
            if self.list_stack:
                self.list_stack.pop()
        elif tag == 'li':
            if self.list_stack:
                # Add list item with bullet
                self.converter.add_paragraph(f"• {self.current_data}", 'Normal')
            else:
                self.converter.add_paragraph(self.current_data, 'Normal')
        elif tag == 'table':
            self.in_table = False
            self.converter.add_table(self.table_headers, self.table_rows)
        elif tag == 'tr':
            self.in_tr = False
            if self.in_table:
                if self.table_headers and not self.table_rows:
                    # First row is header? No, headers are in th
                    pass
                else:
                    self.table_rows.append(self.current_row)
        elif tag == 'th':
            self.in_th = False
            self.table_headers.append(self.current_data.strip())
        elif tag == 'td':
            self.in_td = False
            self.current_row.append(self.current_data.strip())
        elif tag == 'blockquote':
            self.in_blockquote = False
            self.converter.add_paragraph(self.blockquote_text, 'BlockQuote')

    def handle_data(self, data):
        if self.in_pre:
            self.pre_text += data
        elif self.in_blockquote:
            self.blockquote_text += data
        elif self.in_th:
            self.current_data += data
        elif self.in_td:
            self.current_data += data
        else:
            self.current_data += data

# Convert
converter = HTMLToReportLab()
parser = MyHTMLParser(converter)
parser.feed(html)
parser.close()

# Build PDF
doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=letter,
                        rightMargin=72, leftMargin=72,
                        topMargin=72, bottomMargin=72)
doc.build(converter.elements)
print(f"[+] PDF generated: {OUTPUT_PDF}")
