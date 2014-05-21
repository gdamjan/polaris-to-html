#! /usr/bin/env python3

from lxml import html, etree
from lxml.html import builder as E
import re, os, sys, subprocess

def parse_html(fname):
    return html.parse(fname)
    # none of these works:
    #from bs4 import BeautifulSoup
    #return BeautifulSoup(open('naslov.html', 'rb'), "lxml")
    #import html5lib
    #parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"), namespaceHTMLElements=False, strict=False)
    #return parser.parse(open(fname, 'rb'))

def reformat_chapter(chapter):
    # this is where the content is, ignore all else of the file
    content = chapter.xpath('.//center/table//tr/td/*')
    header = content[0]
    header.text = header.text.strip()
    yield header

    paragraphs = content[1:]
    # remove leading space from the first line in a paragraph, the proper place for indent is css
    # also replace \r\n with \n on every text node
    for para in paragraphs:
        p = html.Element('p')
        p.text = para.text.lstrip().replace('\r\n', '\n')
        if para.tail:
            p.tail = para.tail.replace('\r\n', '\n')
        yield p
        for el in para:
            if el.tag == 'br':
                # create new paragraph for each <br> tag
                p = html.Element('p')
                if el.tail:
                    p.text = el.tail.lstrip().replace('\r\n', '\n')
                p.tail = '\n'
                yield p
            else:
                # if this is not a br element, just add it to the last <P> element
                if el.text:
                    el.text = el.text.replace('\r\n', '\n')
                if el.tail:
                    el.tail = el.tail.replace('\r\n', '\n')
                p.append(el)

def get_content_from_files(index='menu.html'):
    index_doc = parse_html(index)
    index_body = index_doc.getroot().find('body')
    for fname in index_body.xpath('.//table//tr/td/p/a/@href'):
        chapter = parse_html(fname)
        yield from reformat_chapter(chapter)


def extract_metadata(fname='naslov.html'):
    meta = {}

    doc = parse_html(fname)
    head = doc.getroot().find('head')

    def reverse_last_first_name(author):
        return ' '.join(reversed(author.split(' ', 1))).strip()

    authors, _, title = head.find('title').text.rpartition(',')
    meta['authors'] = ' & '.join([ reverse_last_first_name(author) for author in authors.split('/')])
    meta['title'] = title.strip().title()

    content = doc.xpath('.//table//tr/td[1]/font[1]')[0]

    meta['coverpage-author(s)'] = content[0].text.strip()
    meta['coverpage-title'] = content[1][0][0].text.strip()
    meta['coverpage-translator'] = content[1][0][2].text.strip()
    meta['coverpage-origtitle'] = content[1][0][2][0].text.strip()

    try:
        el = content.xpath('.//font/p[2]/font')[0]
        series = el.text.strip()
        meta['series'] = re.match(r'Serija "(.*)"', series).group(1)
        series_index = el[0].tail.strip()
        meta['series_index'] = re.match(r'\((\d*)\)', series_index).group(1)
    except:
        pass

    try:
        meta['publisher'] = content.xpath('.//font[last()]')[0].text.strip()
        meta['pubdate'] = content.xpath('.//br[last()]')[0].tail.strip()
    except:
        pass

    # take the last image of the second table cell
    img = doc.xpath('.//img[last()]')[0]
    meta['cover-image'] = img.attrib['src']
    return meta

def create_cover_page(meta):
    cover = E.DIV(E.CLASS('my-cover-page'),
        E.DIV(E.CLASS('title'), meta['coverpage-title']),
        E.DIV(E.CLASS('authors'), meta['coverpage-author(s)']),
        E.DIV(E.CLASS('translator'), meta['coverpage-translator']),
        E.DIV(E.CLASS('orig-title'), meta['coverpage-origtitle'])
    )
    if 'series' in meta:
        series_index = meta.get('series_index', '')
        cover.append(E.DIV(E.CLASS('series'),
            meta['series'], ' - (%s)' % series_index if series_index else ''
        ))
    cover.append(E.HR())
    if 'publisher' in meta:
        pubdate = meta.get('pubdate', '')
        cover.append(E.DIV(E.CLASS('publisher'),
            meta['publisher'], ' - %s' % pubdate if pubdate else ''
        ))
    return cover


def create_head(meta):
    head = html.Element('head')
    etree.SubElement(head, 'meta', charset='utf-8')
    etree.SubElement(head, 'title').text = meta['title']
    etree.SubElement(head, 'meta', name='Author', content=meta['authors'])
    etree.SubElement(head, 'meta', name='cover-image', content=meta['cover-image'])
    etree.SubElement(head, 'meta', name='dc.language', content='sr')
    if 'publisher' in meta:
        etree.SubElement(head, 'meta', name='dc.publisher', content=meta['publisher'])
    if 'pubdate' in meta:
        etree.SubElement(head, 'meta', name='dc.date.published', content=meta['pubdate'])
    if 'series' in meta:
        etree.SubElement(head, 'meta', name='series', content=meta['series'])
    if 'series_index' in meta:
        etree.SubElement(head, 'meta', name='series_index', content=meta['series_index'])
    return head


def create_document():
    meta = extract_metadata()
    head = create_head(meta)

    body = html.Element('body')
    body.append(create_cover_page(meta))
    body.extend(get_content_from_files())

    doc = html.Element('html')
    doc.append(head)
    doc.append(body)
    return doc, meta

def ebook_convert(format, meta):
    ebook_fname = '%s.%s' % (meta['title'], format)
    cmd = ['ebook-convert', 'single-page-book.html', ebook_fname,
         '--cover', meta['cover-image'],
         '--level1-toc', meta['level1-toc'],
         '--level2-toc', meta['level2-toc'],
         '--level3-toc', meta['level3-toc'],
         "--page-breaks-before=//*[name()='h2' or name()='h3']"
    ]
    if 'series' in meta:
        cmd.append('--series=%s' % meta['series'])
    if 'series_index' in meta:
        cmd.append('--series-index=%s' % meta['series_index'])
    subprocess.call(cmd)

if __name__ == '__main__':
    doc, meta = create_document()
    tree = etree.ElementTree(doc)
    if len(doc.xpath('.//h1')) > 0:
        meta['level1-toc'] = '//h:h1'
        meta['level2-toc'] = '//h:h2'
        meta['level3-toc'] = '//h:h3'
    elif len(doc.xpath('.//h2')) > 0:
        meta['level1-toc'] = '//h:h2'
        meta['level2-toc'] = '//h:h3'
        meta['level3-toc'] = '//h:h4'
    else:
        meta['level1-toc'] = '//h:h3'
        meta['level2-toc'] = '//h:h4'
        meta['level3-toc'] = '//h:h5'

    with open('single-page-book.html', 'wb') as out:
        out.write(html.tostring(tree, method='html', encoding='utf-8',
                                pretty_print=True,
                                doctype='<!DOCTYPE html>'))
    if '--azw3' in sys.argv:
        ebook_convert('azw3', meta)
    if '--epub' in sys.argv:
        ebook_convert('epub', meta)
