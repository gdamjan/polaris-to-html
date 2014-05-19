#! /usr/bin/env python

from lxml import html, etree
import re

def get_content_from_files(index='menu.html'):
    index_doc = html.parse(index)
    index_body = index_doc.getroot().body
    for fname in index_body.xpath('.//table/tr/td/p/a/@href'):
        doc = html.parse(fname)
        # this is where the content is:
        yield from doc.xpath('.//center/table/tr/td/*')


def parse_naslov_html(fname='naslov.html'):
    meta = {}

    doc = html.parse(fname)
    head = doc.getroot().head

    def reverse_last_first_name(author):
        return ' '.join(reversed(author.split(' '))).strip()

    authors, title = head.find('title').text.rsplit(',', 1)
    meta['authors'] = ' & '.join([ reverse_last_first_name(author) for author in authors.split('/')])
    meta['title'] = title.strip().title()

    td1, td2 = doc.xpath('.//table/tr/td')

    # remove any images from the result
    for el in td1.xpath('.//img'):
        el.drop_tree()

    series, series_index = doc.xpath('.//table/tr/td/font/p/font/font/p/font[1]/text()')
    meta['series'] = re.match(r'Serija "(.*)"', series.strip()).group(1)
    meta['series_index'] = re.match(r'\((\d*)\)', series_index.strip()).group(1)

    publisher, pubdate = doc.xpath('.//table/tr/td/font/p/font/font/p[2]/font/p/font/text()')
    meta['publisher'] = publisher.strip()
    meta['pubdate'] = pubdate.strip()

    ## take the last image of the second table cell and add it to the result
    #img = td2.xpath('.//img')[-1]
    #img.attrib['src'] = img.attrib['src'].rsplit('/')[-1]
    #td1.append(img)
    return meta, td1.iterchildren()


def create_head(meta):
    head = etree.Element('head')
    etree.SubElement(head, 'meta', charset='utf-8')
    etree.SubElement(head, 'meta', name='dc.language', content='sr')
    etree.SubElement(head, 'meta', name='dc.publisher', content=meta['publisher'])
    etree.SubElement(head, 'meta', name='dc.pubdate', content=meta['pubdate'])
    etree.SubElement(head, 'meta', name='Author', content=meta['authors'])
    etree.SubElement(head, 'title').text = meta['title']
    return head


def create_document():
    meta, front_page_content = parse_naslov_html()
    head = create_head(meta)

    body = etree.Element('body')
    body.extend(front_page_content)
    body.extend(get_content_from_files())

    doc = etree.Element('html')
    doc.append(head)
    doc.append(body)
    return doc


if __name__ == '__main__':
    doc = create_document()
    with open('single-page-book.html', 'wb') as out:
        out.write(html.tostring(doc, method='html', encoding='utf-8',
                                pretty_print=True,
                                doctype='<!DOCTYPE html>'))
