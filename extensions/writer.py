#!/usr/bin/env python
#coding:utf-8
import re
import textwrap

from docutils import nodes, writers

from sphinx import addnodes
from sphinx.locale import admonitionlabels, versionlabels
from sphinx.writers.text import TextWriter, TextTranslator


class BloggerWriter(TextWriter):
    def translate(self):
        visitor = BloggerTranslator(self.document, self.builder)
        self.document.walkabout(visitor)
        self.output = visitor.body



# monkey-patch from TextTranslator
new_wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
        r'(?<=\s)(?::[a-z-]+:)?`\S+|'             # interpreted text start
        r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash
textwrap.TextWrapper.wordsep_re = new_wordsep_re

MAXWIDTH = 70
STDINDENT = 3



class BloggerTranslator(nodes.NodeVisitor):
    sectionchars = '*=-~"+'

    def __init__(self, document, builder):
        nodes.NodeVisitor.__init__(self, document)

        self.states = [[]]
        self.stateindent = [0]
        self.sectionlevel = 0
        self.table = None
        self.do_not_start_state_on_paragraph = False

    def add_text(self, text):
        self.states[-1].append((-1, text))
    def new_state(self, indent=STDINDENT):
        self.states.append([])
        self.stateindent.append(indent)
    def end_state(self, wrap=False, end=[''], first=None):
        # override: never wrap.
        content = self.states.pop()
        maxindent = sum(self.stateindent)
        indent = self.stateindent.pop()
        result = []
        toformat = []
        def do_format():
            if not toformat:
                return
            if wrap:
                res = textwrap.wrap(u''.join(toformat), width=MAXWIDTH-maxindent)
            else:
                res = u''.join(toformat).splitlines()
            if end:
                res += end
            result.append((indent, res))
        for itemindent, item in content:
            if itemindent == -1:
                toformat.append(item)
            else:
                do_format()
                result.append((indent + itemindent, item))
                toformat = []
        do_format()
        if first is not None and result:
            itemindent, item = result[0]
            if item:
                result.insert(0, (itemindent - indent, [first + item[0]]))
                result[1] = (itemindent, item[1:])
        self.states[-1].extend(result)



    def visit_document(self, node):
        self.new_state(0)
    def depart_document(self, node):
        self.end_state()
        self.body = '\n'.join(line and (' '*indent + line)
                              for indent, lines in self.states[0]
                              for line in lines)


    # section and titles
    # e.g.
    # 
    # this is title and section
    # -------------------------
    #
    def visit_section(self, node):
        pass
    def depart_section(self, node):
        pass

    def visit_title(self, node):
        self.add_text(u'\n<span style="font-weight:bold; font-size:110%;">■')
    def depart_title(self, node):
        self.add_text(u'</span>')

    def visit_subtitle(self, node):
        pass
    def depart_subtitle(self, node):
        pass

    def visit_attribution(self, node):
        self.add_text('-- ')
    def depart_attribution(self, node):
        pass

    def visit_desc(self, node):
        self.add_text('<dl>')
    def depart_desc(self, node):
        self.add_text('</dl>')
        self.do_not_start_state_on_paragraph = True

    def visit_desc_signature(self, node):
        self.new_state(0)
        self.add_text('<dt>')
    def depart_desc_signature(self, node):
        # XXX: wrap signatures in a way that makes sense
        self.end_state(wrap=False, end='</dt>')

    def visit_refcount(self, node):
        pass
    def depart_refcount(self, node):
        pass

    def visit_desc_content(self, node):
        self.new_state()
        self.add_text('<dd>')
    def depart_desc_content(self, node):
        self.end_state(end='</dd>')

    def visit_productionlist(self, node):
        self.new_state()
        names = []
        for production in node:
            names.append(production['tokenname'])
        maxlen = max(len(name) for name in names)
        for production in node:
            if production['tokenname']:
                self.add_text(production['tokenname'].ljust(maxlen) + ' ::=')
                lastname = production['tokenname']
            else:
                self.add_text('%s    ' % (' '*len(lastname)))
            self.add_text(production.astext() + '\n')
        self.end_state(wrap=False)
        raise nodes.SkipNode

    def visit_seealso(self, node):
        self.new_state()
    def depart_seealso(self, node):
        self.end_state(first='')

    def visit_footnote(self, node):
        self._footnote = node.children[0].astext().strip()
        self.new_state(len(self._footnote) + 3)
    def depart_footnote(self, node):
        self.end_state(first='[%s] ' % self._footnote)

    def visit_citation(self, node):
        if len(node) and isinstance(node[0], nodes.label):
            self._citlabel = node[0].astext()
        else:
            self._citlabel = ''
        self.new_state(len(self._citlabel) + 3)
    def depart_citation(self, node):
        self.end_state(first='[%s] ' % self._citlabel)

    def visit_label(self, node):
        raise nodes.SkipNode

    def visit_description(self, node):
        pass
    def depart_description(self, node):
        pass

    def visit_tabular_col_spec(self, node):
        raise nodes.SkipNode

    def visit_colspec(self, node):
        self.table[0].append(node['colwidth'])
        raise nodes.SkipNode

    def visit_tgroup(self, node):
        pass
    def depart_tgroup(self, node):
        pass

    def visit_thead(self, node):
        pass
    def depart_thead(self, node):
        pass

    def visit_tbody(self, node):
        self.table.append('sep')
    def depart_tbody(self, node):
        pass

    def visit_row(self, node):
        self.table.append([])
    def depart_row(self, node):
        pass

    def visit_entry(self, node):
        if node.has_key('morerows') or node.has_key('morecols'):
            raise NotImplementedError('Column or row spanning cells are '
                                      'not implemented.')
        self.new_state(0)
    def depart_entry(self, node):
        text = '\n'.join('\n'.join(x[1]) for x in self.states.pop())
        self.stateindent.pop()
        self.table[-1].append(text)

    def visit_table(self, node):
        if self.table:
            raise NotImplementedError('Nested tables are not supported.')
        self.new_state(0)
        self.table = [[]]
    def depart_table(self, node):
        lines = self.table[1:]
        fmted_rows = []
        colwidths = self.table[0]
        realwidths = colwidths[:]
        separator = 0
        # don't allow paragraphs in table cells for now
        for line in lines:
            if line == 'sep':
                separator = len(fmted_rows)
            else:
                cells = []
                for i, cell in enumerate(line):
                    par = textwrap.wrap(cell, width=colwidths[i])
                    if par:
                        maxwidth = max(map(len, par))
                    else:
                        maxwidth = 0
                    realwidths[i] = max(realwidths[i], maxwidth)
                    cells.append(par)
                fmted_rows.append(cells)

        def writesep(char='-'):
            out = ['+']
            for width in realwidths:
                out.append(char * (width+2))
                out.append('+')
            self.add_text(''.join(out) + '\n')

        def writerow(row):
            lines = map(None, *row)
            for line in lines:
                out = ['|']
                for i, cell in enumerate(line):
                    if cell:
                        out.append(' ' + cell.ljust(realwidths[i]+1))
                    else:
                        out.append(' ' * (realwidths[i] + 2))
                    out.append('|')
                self.add_text(''.join(out) + '\n')

        for i, row in enumerate(fmted_rows):
            if separator and i == separator:
                writesep('=')
            else:
                writesep('-')
            writerow(row)
        writesep('-')
        self.table = None
        self.end_state(wrap=False)


    def visit_bullet_list(self, node):
        self._list_counter = -1
        self.add_text('<ul>')
    def depart_bullet_list(self, node):
        self.add_text('</ul>')
        self.do_not_start_state_on_paragraph = True

    def visit_enumerated_list(self, node):
        self._list_counter = 0
        self.add_text('<ol>')
    def depart_enumerated_list(self, node):
        self.add_text('</ol>')
        self.do_not_start_state_on_paragraph = True

    def visit_definition_list(self, node):
        self._list_counter = -2
        self.add_text('<dl>')
    def depart_definition_list(self, node):
        self.add_text('</dl>')
        self.do_not_start_state_on_paragraph = True

    def visit_list_item(self, node):
        if self._list_counter == -1:
            # bullet list
            self.add_text('<li>')
        elif self._list_counter == -2:
            # definition list
            self.add_text('<dd>')
        else:
            # enumerated list
            self._list_counter += 1
            self.add_text('<li>')
    def depart_list_item(self, node):
        if self._list_counter == -1:
            self.add_text('</li>')
        elif self._list_counter == -2:
            self.add_text('</dd>')
        else:
            self.add_text('</li>')

    def visit_definition_list_item(self, node):
        self._li_has_classifier = len(node) >= 2 and \
                                  isinstance(node[1], nodes.classifier)
    def depart_definition_list_item(self, node):
        pass

    def visit_term(self, node):
        self.add_text('<dt>')
        #self.new_state(0)
    def depart_term(self, node):
        self.add_text('</dt>')
        #if not self._li_has_classifier:
        #    self.end_state(end=None)

    def visit_classifier(self, node):
        self.add_text(' : ')
    def depart_classifier(self, node):
        self.end_state(end=None)

    def visit_definition(self, node):
        self.add_text('<dd>')
    def depart_definition(self, node):
        self.add_text('</dd>')

    def visit_field_list(self, node):
        pass
    def depart_field_list(self, node):
        pass

    def visit_field(self, node):
        pass
    def depart_field(self, node):
        pass

    def visit_field_name(self, node):
        self.new_state(0)
    def depart_field_name(self, node):
        self.add_text(':')
        self.end_state(end=None)

    def visit_field_body(self, node):
        self.new_state()
    def depart_field_body(self, node):
        self.end_state()

    def visit_centered(self, node):
        pass
    def depart_centered(self, node):
        pass

    def visit_hlist(self, node):
        pass
    def depart_hlist(self, node):
        pass

    def visit_hlistcol(self, node):
        pass
    def depart_hlistcol(self, node):
        pass

    def visit_admonition(self, node):
        self.new_state(0)
    def depart_admonition(self, node):
        self.end_state()

    def _visit_admonition(self, node):
        self.new_state(2)
    def _make_depart_admonition(name):
        def depart_admonition(self, node):
            self.end_state(first=admonitionlabels[name] + ': ')
        return depart_admonition

    visit_attention = _visit_admonition
    depart_attention = _make_depart_admonition('attention')
    visit_caution = _visit_admonition
    depart_caution = _make_depart_admonition('caution')
    visit_danger = _visit_admonition
    depart_danger = _make_depart_admonition('danger')
    visit_error = _visit_admonition
    depart_error = _make_depart_admonition('error')
    visit_hint = _visit_admonition
    depart_hint = _make_depart_admonition('hint')
    visit_important = _visit_admonition
    depart_important = _make_depart_admonition('important')
    visit_note = _visit_admonition
    depart_note = _make_depart_admonition('note')
    visit_tip = _visit_admonition
    depart_tip = _make_depart_admonition('tip')
    visit_warning = _visit_admonition
    depart_warning = _make_depart_admonition('warning')

    def visit_versionmodified(self, node):
        self.new_state(0)
        if node.children:
            self.add_text(versionlabels[node['type']] % node['version'] + ': ')
        else:
            self.add_text(versionlabels[node['type']] % node['version'] + '.')
    def depart_versionmodified(self, node):
        self.end_state()

    def visit_literal_block(self, node):
        self.add_text('<pre>')
    def depart_literal_block(self, node):
        self.add_text('</pre>')
        self.do_not_start_state_on_paragraph = True

    def visit_doctest_block(self, node):
        self.new_state(0)
    def depart_doctest_block(self, node):
        self.end_state(wrap=False)

    def visit_line_block(self, node):
        self.new_state(0)
    def depart_line_block(self, node):
        self.end_state(wrap=False)

    def visit_line(self, node):
        pass
    def depart_line(self, node):
        pass

    def visit_block_quote(self, node):
        self.add_text('<blockquote>')
    def depart_block_quote(self, node):
        self.add_text('</blockquote>')

    def visit_compact_paragraph(self, node):
        pass
    def depart_compact_paragraph(self, node):
        pass

    def visit_paragraph(self, node):
        if isinstance(node.parent, nodes.bullet_list) or \
           isinstance(node.parent, nodes.enumerated_list) or \
           isinstance(node.parent, nodes.definition_list) or \
           isinstance(node.parent, nodes.definition_list_item) or \
           isinstance(node.parent, nodes.term) or \
           isinstance(node.parent, nodes.definition) or \
           isinstance(node.parent, nodes.list_item) or \
           False:
            return
        if self.do_not_start_state_on_paragraph:
            return
        if not isinstance(node.parent, nodes.Admonition) or \
               isinstance(node.parent, addnodes.seealso):
            self.new_state(0)
    def depart_paragraph(self, node):
        if isinstance(node.parent, nodes.bullet_list) or \
           isinstance(node.parent, nodes.enumerated_list) or \
           isinstance(node.parent, nodes.definition_list) or \
           isinstance(node.parent, nodes.definition_list_item) or \
           isinstance(node.parent, nodes.term) or \
           isinstance(node.parent, nodes.definition) or \
           isinstance(node.parent, nodes.list_item) or \
           False:
            return
        if self.do_not_start_state_on_paragraph:
            self.do_not_start_state_on_paragraph = False
            return
        if not isinstance(node.parent, nodes.Admonition) or \
               isinstance(node.parent, addnodes.seealso):
            self.end_state()

    def visit_target(self, node):
        raise nodes.SkipNode

    def visit_index(self, node):
        raise nodes.SkipNode

    def visit_substitution_definition(self, node):
        raise nodes.SkipNode

    def visit_pending_xref(self, node):
        pass
    def depart_pending_xref(self, node):
        pass

    def visit_reference(self, node):
        if node.hasattr('refuri'):
            self.add_text('<a href="%s">' % node['refuri'])
        elif node.hasattr('refid'):
            self.add_text('<a href="%s">' % node['refid'])
        
    def depart_reference(self, node):
        self.add_text('</a>')

    def visit_download_reference(self, node):
        self.visit_reference(node)
    def depart_download_reference(self, node):
        self.depart_reference(node)

    def visit_emphasis(self, node):
        self.add_text('<span style="font-weight:bold;">')
    def depart_emphasis(self, node):
        self.add_text('</span>')

    def visit_literal_emphasis(self, node):
        self.add_text('<span style="font-weight:bold;">')
    def depart_literal_emphasis(self, node):
        self.add_text('</span>')

    def visit_strong(self, node):
        self.add_text('<span style="font-weight:bold; color:#cc0000;">')
    def depart_strong(self, node):
        self.add_text('</span>')

    def visit_abbreviation(self, node):
        self.add_text('')
    def depart_abbreviation(self, node):
        if node.hasattr('explanation'):
            self.add_text(' (%s)' % node['explanation'])

    def visit_title_reference(self, node):
        self.add_text('*')
    def depart_title_reference(self, node):
        self.add_text('*')

    def visit_literal(self, node):
        self.add_text('<code>')
    def depart_literal(self, node):
        self.add_text('</code>')

    def visit_subscript(self, node):
        self.add_text('_')
    def depart_subscript(self, node):
        pass

    def visit_superscript(self, node):
        self.add_text('^')
    def depart_superscript(self, node):
        pass

    def visit_footnote_reference(self, node):
        self.add_text('[%s]' % node.astext())
        raise nodes.SkipNode

    def visit_citation_reference(self, node):
        self.add_text('[%s]' % node.astext())
        raise nodes.SkipNode

    def visit_Text(self, node):
        self.add_text(node.astext())
    def depart_Text(self, node):
        pass

    def visit_generated(self, node):
        pass
    def depart_generated(self, node):
        pass

    def visit_inline(self, node):
        pass
    def depart_inline(self, node):
        pass

    def visit_problematic(self, node):
        self.add_text('>>')
    def depart_problematic(self, node):
        self.add_text('<<')

    def visit_system_message(self, node):
        self.new_state(0)
        self.add_text('<SYSTEM MESSAGE: %s>' % node.astext())
        self.end_state()
        raise nodes.SkipNode

    def visit_comment(self, node):
        raise nodes.SkipNode

    def visit_meta(self, node):
        # only valid for HTML
        raise nodes.SkipNode

    def unknown_visit(self, node):
        raise NotImplementedError('Unknown node: ' + node.__class__.__name__)
