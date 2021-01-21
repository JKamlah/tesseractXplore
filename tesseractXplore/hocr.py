#!/usr/bin/env python

# extract the images and texts within all the ocr_line elements
# within the hOCR file

from __future__ import print_function

import re

from lxml import html


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


def save_hocr(hocr, data, *args):
    doc = html.parse(hocr)
    data = {line.line: data for line in data if line.edited == True}
    pages = doc.xpath('//*[@class="ocr_page"]')
    result = {}
    for page in pages:
        pars = page.xpath("//*[@class='ocr_par']")
        for par in pars:
            lines = par.xpath("//*[@class='ocr_line']")
            lcount = 1
            for line in lines:
                words = line.xpath("//*[@class='ocrx_word']")
                if lcount in data.keys():
                    bbox = [int(x) for x in get_prop(line, 'bbox').split()]
                    if bbox[0] > bbox[2] or bbox[1] >= bbox[3]:
                        continue
                    result[lcount] = {'text': get_text(line), 'bbox': bbox}
                lcount += 1
                # if words:
                #    for word in words:
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
                words = line.xpath("*[@class='ocrx_word']")
                lcount += 1
                if words:
                    for word in words:
                        result[par.get('id')][line.get('id')][word.get('id')] = {'text': get_text(word),
                                                                                 'bbox': get_prop(word, 'bbox')}
    return result
