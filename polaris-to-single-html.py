#! /usr/bin/env python

from lxml import html, etree


def get_content_from_files(index='menu.html'):
    index_doc = html.parse(index)
    index_body = index_doc.getroot().body
    for fname in index_body.xpath('.//table/tr/td/p/a/@href'):
        doc = html.parse(fname)
        # this is where the content is:
        yield from doc.xpath('.//center/table/tr/td/*')


def parse_naslov_html(fname='naslov.html'):
    doc = html.parse(fname)
    head = doc.getroot().head
    title  = head.find('title')

    td1, td2 = doc.xpath('.//table/tr/td')

    # remove any images from the result
    for el in td1.xpath('.//img'):
        el.drop_tree()

    ## take the last image of the second table cell and add it to the result
    #img = td2.xpath('.//img')[-1]
    #img.attrib['src'] = img.attrib['src'].rsplit('/')[-1]
    #td1.append(img)
    return title, td1.iterchildren()


def create_head(orig_title):
    authors, title = orig_title.rsplit(',', 1)
    head = etree.Element('head')
    charset = etree.SubElement(head, 'meta')
    charset.attrib['charset'] = 'utf-8'
    for author in authors.split('/'):
        author_el = etree.SubElement(head, 'meta')
        author_el.attrib['name'] = 'Author'
        # reverse sur-name given-name
        author_el.attrib['content'] = ' '.join(reversed(author.split(' '))).strip()
    title_el = etree.SubElement(head, 'title')
    title_el.text = title.title().strip()
    return head


def create_document():
    title, front_page = parse_naslov_html()
    head = create_head(title.text)

    body = etree.Element('body')
    body.extend(front_page)
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
