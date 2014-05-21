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
    header, paragraphs = chapter.xpath('.//center/table//tr/td/*')
    header.text = header.text.strip()
    yield header
    p = html.Element('p')
    p.text = paragraphs.text.strip()
    yield p
    for el in paragraphs:
        p = html.Element('p')
        if el.tag == 'br':
            p.text = el.tail.strip()
        else:
            p.append(el)
        yield p

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
        return ' '.join(reversed(author.split(' '))).strip()

    authors, title = head.find('title').text.rsplit(',', 1)
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
    cover = E.DIV(E.CLASS('cover-page'),
        E.DIV(meta['coverpage-author(s)']),
        E.H1(meta['coverpage-title']),
        E.DIV(meta['coverpage-translator']),
        E.DIV(meta['coverpage-origtitle'])
    )
    if 'series' in meta:
        series_index = meta.get('series_index', '')
        cover.append(E.DIV(
            meta['series'], ' - (%s)' % series_index if series_index else ''
        ))
    cover.append(E.HR())
    if 'publisher' in meta:
        pubdate = meta.get('pubdate', '')
        cover.append(E.DIV(
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


if __name__ == '__main__':
    doc, meta = create_document()
    tree = etree.ElementTree(doc)
    with open('single-page-book.html', 'wb') as out:
        out.write(html.tostring(tree, method='html', encoding='utf-8',
                                pretty_print=True,
                                doctype='<!DOCTYPE html>'))
    if '--azw3' in sys.argv:
        cmd = ['ebook-convert', 'single-page-book.html', '%s.azw3' % meta['title'],
             '--cover', meta['cover-image'],
             '--level1-toc=//h:h2',
             '--level2-toc=//h:h3',
             "--page-breaks-before=//*[name()='h2' or name()='h3']"]
        if 'series' in meta:
            cmd.append('--series=%s' % meta['series'])
        if 'series_index' in meta:
            cmd.append('--series-index=%s' % meta['series_index'])
        subprocess.call(cmd)
