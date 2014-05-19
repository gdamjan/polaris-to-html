#! /usr/bin/env python

from lxml import html, etree

from glob import iglob

def get_content_from_files(glob="p*.html"):
    for fname in sorted(iglob(glob), key=lambda fn: int(fn[1:-5])):
        doc = html.parse(fname)
        body = doc.getroot().body
        # this is where the content is:
        yield from body.xpath('.//center/table/tr/td/*')


def get_title_naslovna():
    doc = html.parse('naslov.html')
    head = doc.getroot().head
    title  = head.find('title')

    body = doc.getroot().body
    td1, td2 = body.xpath('.//table/tr/td')

    # remove any images from the result
    for el in td1.xpath('.//img'):
        el.drop_tree()

    # take the last image of the second table cell and add it to the result
    img = td2.xpath('.//img')[-1]
    img.attrib['src'] = img.attrib['src'].rsplit('/')[-1]
    td1.append(img)
    return title, td1


def main():
    page = etree.Element('html')
    doc = etree.ElementTree(page)
    head = etree.SubElement(page, 'head')
    meta = etree.SubElement(head, 'meta')
    meta.attrib['charset'] = 'utf-8'

    body = etree.SubElement(page, 'body')

    title, naslovna = get_title_naslovna()
    head.append(title)
    for el in naslovna:
        body.append(el)

    for el in get_content_from_files():
        body.append(el)

    outFile = open('single-page-book.html', 'wb')
    doc.write(outFile, encoding='utf-8', method='html', pretty_print=True)

if __name__ == '__main__':
    main()
