#!/usr/bin/env python

# extract the images and texts within all the ocr_line elements
# within the hOCR file

from __future__ import print_function

import re

from lxml import html
from lxml import etree


def get_text(node):
    textnodes = node.xpath('.//text()')
    s = ''.join([text for text in textnodes]).strip()
    return re.sub(r'\s+', ' ', s)


def get_prop(node, name):
    title = node.get("title")
    props = title.split(';')
    for prop in props:
        (key, args) = prop.split(None, 1)
        args = args.strip('"')
        if key == name:
            return args
    return None

def set_prop(node, name, val):
    title = node.get("title")
    props = title.split(';')
    for idx, prop in enumerate(props):
        (key, args) = prop.split(None, 1)
        args = args.strip('"')
        if key == name:
            args = val
        props[idx] = key+' '+args
    node.set("title","; ".join(props))
    return None


def save_hocr(hocr, data, *args):
    doc = html.parse(hocr)
    data = {line.line_id: line for line in data}
    pages = doc.xpath('//*[@class="ocr_page"]')
    result = {}
    for page in pages:
        pars = page.xpath("//*[@class='ocr_par']")
        for par in pars:
            lines = par.xpath("//*[@class='ocr_line']")
            for line in lines:
                line.text = data[line.attrib["id"]].text
                set_prop(line, "bbox", " ".join([str(num) for num in data[line.attrib["id"]].bbox]))
                for word in list(line):
                    line.remove(word)
    with open(hocr, "w") as f:
        f.writelines(etree.tostring(doc, pretty_print=True).decode('UTF-8'))
    return result


def get_text_and_bbox(hocr, padding=4):
    doc = html.parse(hocr)
    pages = doc.xpath('//*[@class="ocr_page"]')
    result = {}
    for page in pages:
        pars = page.xpath("//*[@class='ocr_par']")
        for par in pars:
            result[par.get('id')] = {}
            lines = par.xpath("*[@class='ocr_line']")
            lcount = 1
            for line in lines:
                result[par.get('id')][line.get('id')] = {}
                result[par.get('id')][line.get('id')]['text'] = get_text(line)
                result[par.get('id')][line.get('id')]['bbox'] = [int(x) for x in get_prop(line, 'bbox').split()]
                lcount += 1
                words = line.xpath("*[@class='ocrx_word']")
                if words:
                     for word in words:
                         result[par.get('id')][line.get('id')][word.get('id')] = {'text': get_text(word),
                                                                                  'bbox': get_prop(word, 'bbox')}
    return result
