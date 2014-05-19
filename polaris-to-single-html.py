#! /usr/bin/env python

from lxml import html, etree

from glob import iglob

def get_content_from_files(glob="p*.html"):
    for fname in sorted(iglob(glob), key=lambda fn: int(fn[1:-5])):
        doc = html.parse(fname)
        body = doc.getroot().body
        # this is where the content is:
        yield from body.xpath('.//center/table/tr/td/*')

def get_meta_info():
    # get meta from 'naslov.html' including image
    return

def main():
    page = etree.Element('html')
    doc = etree.ElementTree(page)
    head = etree.SubElement(page, 'head')
    meta = etree.SubElement(head, 'meta')
    meta.attrib['charset'] = 'utf-8'

    body = etree.SubElement(page, 'body')
    title = etree.SubElement(head, 'title')
    title.text = 'Your page title here'

    for el in get_content_from_files():
        body.append(el)

    outFile = open('the-book.html', 'wb')
    doc.write(outFile, encoding='utf-8', method='html', pretty_print=True)

if __name__ == '__main__':
    main()
