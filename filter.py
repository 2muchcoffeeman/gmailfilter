#!/usr/bin/python
from bs4 import BeautifulSoup
import lxml
import sys

header = "<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:apps='http://schemas.google.com/apps/2006'>" \
         "<title>Mail Filters</title>"


footer = "</feed>"


def main(argz):
    file_name = argz[0]
    soup = BeautifulSoup(open(file_name), "xml")
    print get_name(soup)
    print get_email(soup)


entry_template = \
    "<entry>" \
    "   <category term='filter'></category>" \
    "   <title>{0}</title>" \
    "   <content></content>" \
    "   <apps:property name='from' value='flybuys@edm.flybuys.com.au'/>" \
    "   <apps:property name='label' value='Newsletters'/>" \
    "</entry>"


author_template = "<author>" \
                  "<name>{0}</name>" \
                  "<email>{1}</email>" \
                  "</author>"


def author_xml(name, email):
    return author_template.format(name, email)


def get_name(soup):
    return soup.find_all("name")[0].contents[0]


def get_email(soup):
    return soup.find_all("email")[0].contents[0]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: filter <filter.xml>"
    else:
        main(sys.argv[1:])