#!/usr/bin/python
from bs4 import BeautifulSoup
import lxml
import sys
import os


def main(argz):
    file_name = argz[0]
    mail_filter = MailFilter(file_name)
    print_filters = True
    while 1:
        if print_filters:
            print mail_filter
        command = raw_input("Enter a value:")
        print_filters = mail_filter.process_command(command)


class MailFilter:
    header = "<?xml version='1.0' encoding='UTF-8'?>" \
             "<feed xmlns='http://www.w3.org/2005/Atom' xmlns:apps='http://schemas.google.com/apps/2006'>\n" \
             "<title>Mail Filters</title>\n"
    footer = "</feed>\n"
    author_template = "<author>\n" \
                      "    <name>{0}</name>\n" \
                      "    <email>{1}</email>\n" \
                      "</author>\n"

    def __init__(self, filename):
        self.filename = filename
        soup = BeautifulSoup(open(filename), "xml")
        self.name = soup.find("name").text
        self.email = soup.find("email").text
        self.entries = []
        """
        :type filename string
        :type name string
        :type email string
        :type entries list
        """
        entries_nodes = soup.find_all("entry")
        for e in entries_nodes:
            entry = Entry(e)
            self.entries.append(entry)

    def __repr__(self):
        return "{0} {1}\n".format(self.name, self.email) + \
               ('\n'.join(["{0} {1}".format(idx, repr(e)) for idx, e in enumerate(self.entries)]))

#    def to_xml(self):
#        MailFilter.header
#        MailFilter.author_template.format(self.name, self.email)
#        MailFilter.footer

    # TODO: Can I have variable length arguments and just pass in an array?
    def process_command(self, command):
        """
        :type command: string
        :rtype: boolean
        """
        parts = command.split(" ")
        action = parts[0]

        if action == 'exit':
            sys.exit(0)

        arguments = parts[1:]
        actions = {
            'join': lambda x: self.join_entries(x),
            'remove': lambda x: self.remove(x),
            'save': lambda x: self.save(x),
            'delete': lambda x: self.delete_property(x),
            'add': lambda x: self.add_property(x),
            'search': lambda x: self.search_property(x)
        }

        if action == 'help':
            for action in actions:
                print action
            return False

        elif action in actions:
            return actions[action](arguments)

    def search_property(self, arguments):
        name = arguments[0]
        value = arguments[1]
        for entry in self.entries:
            """
            :type entry Entry
            """
            for prop in entry.properties:
                """
                :type prop Prop
                """
                if prop.name == name and prop.value == value:
                    print entry
                    break
        return False

    def add_property(self, arguments):
        entry_index = int(arguments[0])
        property_to_add = arguments[1:]
        self.entries[entry_index].add_property(property_to_add)
        return True

    def delete_property(self, arguments):
        entry_index = int(arguments[0])
        property_to_remove = arguments[1]
        self.entries[entry_index].remove_property(property_to_remove)
        return True

    def save(self, arguments):
        postfix = 1

        if len(arguments) == 1:
            save_filename = arguments[0]
        else:
            save_filename = '_'.join([self.filename, str(postfix)])
            while os.path.isfile(save_filename):
                postfix += 1
                save_filename = '_'.join([self.filename, str(postfix)])

        file_handler = open(save_filename, 'w')
        # Start writing the file out
        file_handler.write(MailFilter.header)
        file_handler.write(MailFilter.author_template.format(self.name, self.email))
        # Do the entries
        for e in self.entries:
            file_handler.write(e.to_xml())
        file_handler.write(MailFilter.footer)
        file_handler.close()

    # Join the conditions
    def join_entries(self, arguments):
        entries_to_join = [self.entries[int(a)] if int(a) < len(self.entries) else None for a in arguments]
        e1 = entries_to_join[0]
        for e in entries_to_join[1:]:
            if e:
                self.entries.remove(e)
                e1.join_entry(e)

    def remove(self, arguments):
        idx = int(arguments[0])
        self.entries.remove(self.entries[idx])

    def author_xml(self, name, email):
        return self.author_template.format(name, email)


class Entry:
    def __init__(self, entry):
        if entry:
            properties = entry.find_all("property")
            self.properties = [Prop(p['name'], p['value']) for p in properties]
        else:
            self.properties = []
        """
        :type properties list
        """

    def __repr__(self):
        return "".join([repr(p) for p in self.properties])

    def join_entry(self, entry):
        new_props_hash = {p.name: p for p in self.properties}
        for p in entry.properties:
            if p.name in new_props_hash:
                new_p = new_props_hash[p.name].join(p)
                new_props_hash[p.name] = new_p
            else:
                new_props_hash[p.name] = p
        self.properties = [value for value in new_props_hash.itervalues()]

    def to_xml(self):
        props_xml = ''.join([p.to_xml() for p in self.properties])
        return props_xml.join([Entry.entry_template_header, Entry.entry_template_footer])

    def remove_property(self, prop_name):
        matching_properties = [p if p.name == prop_name else None for p in self.properties]
        for p in matching_properties:
            if p:
                self.properties.remove(p)

    def add_property(self, props):
        if len(props) == 0:
            return
        prop = props[0]
        if prop in Entry.properties_with_single_values:
            self.properties.append(Prop(prop, Entry.properties_with_single_values[prop]))
        else:
            self.properties.append(Prop(prop, props[1]))

    properties_with_single_values = {
        'sizeOperator': 's_sl',
        'sizeUnit': 's_smb',
        'shouldMarkAsRead': 'true'
    }

    entry_template_header = \
        "<entry>\n" \
        "    <category term='filter'></category>\n" \
        "    <title>Mail Filter</title>\n" \
        "    <content></content>\n"

    entry_template_footer = "</entry>\n"


class Prop:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        """
        :type name string
        :type value string
        """

    def __repr__(self):
        return "\t{0}:{1}\n".format(self.name, self.value)

    def join(self, prop):
        if not self.can_be_joined():
            return Prop(self.name, self.value)
        if self.name == prop.name:
            return Prop(self.name, ' OR '.join([self.value, prop.value]))
        else:
            return self

    def can_be_joined(self):
        return self.name in Prop.joinable_properties

    def to_xml(self):
        return self.xml[self.name].format(self.value)

    joinable_properties = {'hasTheWord', 'from', 'to'}

    xml = {
        'hasTheWord': "    <apps:property name='hasTheWord' value='{0}'/>\n",
        'from': "    <apps:property name='from' value='{0}'/>\n",
        'to': "    <apps:property name='to' value='{0}'/>\n",

        'sizeOperator': "    <apps:property name='sizeOperator' value='s_sl'/>\n",
        'sizeUnit': "    <apps:property name='sizeUnit' value='s_smb'/>\n",

        'shouldMarkAsRead': "    <apps:property name='shouldMarkAsRead' value='true'/>\n",
        'label': "    <apps:property name='label' value='{0}'/>\n"
    }

    apps_hasTheWord = "<apps:property name='hasTheWord' value='{0}'/>"
    apps_from = "<apps:property name='from' value='{0}'/>"
    apps_to = "<apps:property name='to' value='{0}'/>"

    apps_sizeOperator = "<apps:property name='sizeOperator' value='s_sl'/>"
    apps_sizeUnit = "<apps:property name='sizeUnit' value='s_smb'/>"

    apps_shouldMarkAsRead = "<apps:property name='shouldMarkAsRead' value='true'/>"
    apps_label = "<apps:property name='label' value='{0}'/>"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: filter <filter.xml>")
    else:
        main(sys.argv[1:])
