import re
from ..helpers import PREVENT_BACKSLASH

__all__ = ['table']


TABLE_PATTERN = (
  r'^ {0,3}\|(?P<table_head>.+)\|[ \t]*\n'
  r' {0,3}\|(?P<table_align> *[-:]+[-| :]*)\|[ \t]*\n'
  r'(?P<table_body>(?: {0,3}\|.*\|[ \t]*(?:\n|$))*)\n*'
)
NP_TABLE_PATTERN = (
  r'^ {0,3}(?P<nptable_head>\S.*\|.*)\n'
  r' {0,3}(?P<nptable_align>[-:]+ *\|[-| :]*)\n'
  r'(?P<nptable_body>(?:.*\|.*(?:\n|$))*)\n*'
)

TABLE_CELL = re.compile(r'^ {0,3}\|(.+)\|[ \t]*$')
CELL_SPLIT = re.compile(r' *' + PREVENT_BACKSLASH + r'\| *')
ALIGN_CENTER = re.compile(r'^ *:-+: *$')
ALIGN_LEFT = re.compile(r'^ *:-+ *$')
ALIGN_RIGHT = re.compile(r'^ *-+: *$')


def parse_table(block, m, state):
    pos = m.end()
    header = m.group('table_head')
    align = m.group('table_align')
    thead, aligns = _process_thead(header, align)
    if not thead:
        return

    rows = []
    body = m.group('table_body')
    for text in body.splitlines():
        m = TABLE_CELL.match(text)
        if not m:
            return
        row = _process_row(m.group(1), aligns)
        if not row:
            return
        rows.append(row)

    children = [thead, {'type': 'table_body', 'children': rows}]
    state.append_token({'type': 'table', 'children': children})
    return pos


def parse_nptable(block, m, state):
    header = m.group('nptable_head')
    align = m.group('nptable_align')
    thead, aligns = _process_thead(header, align)
    if not thead:
        return

    rows = []
    body = m.group('nptable_body')
    for text in body.splitlines():
        row = _process_row(text, aligns)
        if not row:
            return
        rows.append(row)

    children = [thead, {'type': 'table_body', 'children': rows}]
    state.append_token({'type': 'table', 'children': children})
    return m.end()


def _process_thead(header, align):
    headers = CELL_SPLIT.split(header)
    aligns = CELL_SPLIT.split(align)
    if len(headers) != len(aligns):
      return None, None

    for i, v in enumerate(aligns):
        if ALIGN_CENTER.match(v):
            aligns[i] = 'center'
        elif ALIGN_LEFT.match(v):
            aligns[i] = 'left'
        elif ALIGN_RIGHT.match(v):
            aligns[i] = 'right'
        else:
            aligns[i] = None

    children = [
        {
            'type': 'table_cell',
            'text': text.strip(),
            'attrs': {'align': aligns[i], 'head': True}
        }
        for i, text in enumerate(headers)
    ]
    thead = {'type': 'table_head', 'children': children}
    return thead, aligns


def _process_row(text, aligns):
    cells = CELL_SPLIT.split(text)
    if len(cells) != len(aligns):
        return None

    children = [
        {
            'type': 'table_cell',
            'text': text.strip(),
            'attrs': {'align': aligns[i], 'head': False}
        }
        for i, text in enumerate(cells)
    ]
    return {'type': 'table_row', 'children': children}


def render_table(renderer, text):
    return '<table>\n' + text + '</table>\n'


def render_table_head(renderer, text):
    return '<thead>\n<tr>\n' + text + '</tr>\n</thead>\n'


def render_table_body(renderer, text):
    return '<tbody>\n' + text + '</tbody>\n'


def render_table_row(renderer, text):
    return '<tr>\n' + text + '</tr>\n'


def render_table_cell(renderer, text, align=None, head=False):
    if head:
        tag = 'th'
    else:
        tag = 'td'

    html = '  <' + tag
    if align:
        html += ' style="text-align:' + align + '"'

    return html + '>' + text + '</' + tag + '>\n'


def table(md):
    md.block.register('table', TABLE_PATTERN, parse_table, before='paragraph')
    md.block.register('nptable', NP_TABLE_PATTERN, parse_nptable, before='paragraph')
    if md.renderer and md.renderer.NAME == 'html':
        md.renderer.register('table', render_table)
        md.renderer.register('table_head', render_table_head)
        md.renderer.register('table_body', render_table_body)
        md.renderer.register('table_row', render_table_row)
        md.renderer.register('table_cell', render_table_cell)
