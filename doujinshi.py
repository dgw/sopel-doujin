# coding=utf-8
"""
doujinshi.py - Sopel doujinshi info plugin
Copyright 2019 dgw
Licensed under the Eiffel Forum License 2

https://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import copy

from lxml import etree
import requests

from sopel import formatting, module


ITEM_TEMPLATE = {
    'site': 'unknown',
    'link': '',
    'title': 'Title Unknown',
    'tags': [],
}


def say_result(bot, item):
    if item['link']:
        item['link'] = ' | ' + item['link']
    if item['tags']:
        item['tags'] = ', '.join(item['tags'])
    else:
        item['tags'] = '(no tags found)'
    bot.say('[{site}] {title} | Tagged: {tags}{link}'.format(**item))


NHENTAI_GALLERY_BASE = 'https://nhentai.net/g/'
NHENTAI_GALLERY_PATTERN = NHENTAI_GALLERY_BASE + r'(\d+)/?'
NHENTAI_GALLERY_TEMPLATE = NHENTAI_GALLERY_BASE + '{id}/'
NHENTAI_SITENAME = 'nhentai'


@module.url(NHENTAI_GALLERY_PATTERN)
def nhentai_link(bot, trigger, match):
    nhentai_info(bot, trigger, match.group(1))


@module.commands('nhentai', 'nh')
def nhentai_info(bot, trigger, id_=None):
    """Fetch information about a gallery on nhentai."""
    link = False
    if not id_:  # commanded
        id_ = trigger.group(3)
        if not id_:  # commanded with no argument
            bot.reply('I need a gallery ID number.')
            return module.NOLIMIT
        else:  # make sure we give a link to the gallery when commanded
            link = True


    # Now the real "fun" begins
    url = NHENTAI_GALLERY_TEMPLATE.format(id=id_)
    try:
        r = requests.get(url=url, timeout=(10.0, 4.0))
    except requests.exceptions.ConnectTimeout:
        return bot.say("[{}] Connection timed out.".format(NHENTAI_SITENAME))
    except requests.exceptions.ConnectionError:
        return bot.say("[{}] Couldn't connect to server.".format(NHENTAI_SITENAME))
    except requests.exceptions.ReadTimeout:
        return bot.say("[{}] Server took too long to send data.".format(NHENTAI_SITENAME))
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return bot.say("[{}] Gallery {} doesn't exist.".format(NHENTAI_SITENAME, id_))
        return bot.say("[{}] HTTP error: ".format(NHENTAI_SITENAME) + str(e.response.status_code))

    page = etree.HTML(r.content)

    item = copy.deepcopy(ITEM_TEMPLATE)
    item['site'] = NHENTAI_SITENAME
    if link:
        item['link'] = url
    
    item['title'] = page.xpath('/html/body/div[2]/div[1]/div[2]/div/h1')[0].text
    item['tags'] = [el.text.strip() for el in page.xpath('//*[@id="tags"]/div[3]/span')[0]]

    say_result(bot, item)
