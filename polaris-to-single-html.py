#! /usr/bin/env python

from lxml import html, etree


def get_content_from_files(index='menu.html'):
    index_doc = html.parse(index)
    index_body = index_doc.getroot().body
    for fname in index_body.xpath('.//table/tr/td/p/a/@href'):
        doc = html.parse(fname)
        body = doc.getroot().body
        # this is where the content is:
        yield from body.xpath('.//center/table/tr/td/*')


def parse_naslov_html(fname='naslov.html'):
    doc = html.parse(fname)
    head = doc.getroot().head
    title  = head.find('title')

    body = doc.getroot().body
    td1, td2 = body.xpath('.//table/tr/td')

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


def main():
    page = etree.Element('html')
    doc = etree.ElementTree(page)

    title, front_page = parse_naslov_html()
    head = create_head(title.text)
    page.append(head)

    body = etree.SubElement(page, 'body')
    body.extend(front_page)
    body.extend(get_content_from_files())

    outFile = open('single-page-book.html', 'wb')
    doc.write(outFile, encoding='utf-8', method='html', pretty_print=True)

if __name__ == '__main__':
    main()
