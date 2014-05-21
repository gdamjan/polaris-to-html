#! /usr/bin/env python3

from lxml import html, etree
import re, os, sys

def parse_html(fname):
    return html.parse(fname)
    # none of these works:
    #from bs4 import BeautifulSoup
    #return BeautifulSoup(open('naslov.html', 'rb'), "lxml")
    #import html5lib
    #parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"), namespaceHTMLElements=False, strict=False)
    #return parser.parse(open(fname, 'rb'))

def get_content_from_files(index='menu.html'):
    index_doc = parse_html(index)
    index_body = index_doc.getroot().find('body')
    for fname in index_body.xpath('.//table//tr/td/p/a/@href'):
        doc = parse_html(fname)
        # this is where the content is:
        yield from doc.xpath('.//center/table//tr/td/*')


def parse_naslov_html(fname='naslov.html'):
    meta = {}

    doc = parse_html(fname)
    head = doc.getroot().find('head')

    def reverse_last_first_name(author):
        return ' '.join(reversed(author.split(' '))).strip()

    authors, title = head.find('title').text.rsplit(',', 1)
    meta['authors'] = ' & '.join([ reverse_last_first_name(author) for author in authors.split('/')])
    meta['title'] = title.strip().title()

    content = doc.xpath('.//table//tr/td[1]')[0]

    # remove any images from the result
    for el in content.xpath('.//img'):
        el.getparent().remove(el)

    try:
        el = content.xpath('.//font/p/font/font/p/font')[0]
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
    return meta, content.iterchildren()


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
    meta, front_page_content = parse_naslov_html()
    head = create_head(meta)

    body = html.Element('body')
    body.extend(front_page_content)
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
    os.symlink(meta['cover-image'], 'cover.jpg')
