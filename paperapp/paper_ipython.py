# -*- coding: utf-8 -*-

import os
import re
import codecs
import yaml
import os
import os.path
import copy
from jinja2 import Environment, PackageLoader

from .paper_yaml import safe_unicode
from .materializer import node_data
from .paper_repo import PaperRepo

import ipywidgets as widgets

def render_node(paper, node_or_key):
    """
    Render a node as jupyter HTML widget.
    """
    if type(node_or_key) is str:
        node = paper[node_or_key]
    else:
        node = node_or_key
    env = Environment(loader=PackageLoader('paperapp', 'templates'))
    template = env.get_template("main_table.html")
    (data, backlinks) = node_data(paper, node)
    html = "<h3>%s - %s</h3>%s" % (node['type'],
                                   node['id'],
                                   template.render(_type=node['type'],
                                                   _id=node['id'], data=data,
                                                   backlinks=backlinks))
    return widgets.HTML(
        value=html
    )

def new_node(paper, _id=None, _type="artifact", upload=False, prototype=None):
    """
    Live editing a newly created paper
    """

    if not _type in paper.get_type_relations():
        return "Unknown type: " + _type

    if _id is None or _id == "":
        if _type == "artifact":
            __type = "paper"
        else:
            __type = _type
        _id = '%s-%d' % (__type, paper.counts_by_type.get(_type, 0) + 1,)
        
    box = widgets.VBox()

    def _set_upload(upload):
        fb = FileBrowser(upload)

        def process_upload(source):
            nf = paper.register_file(fb.path)
            _set_edit(nf['text'],uploaded_file=nf)
        
        done_button = widgets.Button(description="pick file", background_color='#ffd0d0')
        done_button.on_click(process_upload)
        box.children = tuple([fb.widget(), done_button])

    def _set_edit(text, uploaded_file=None):
        node = paper._base_node(_id, _type, text)
        if prototype:
            for k in prototype:
                if not k in set(['id', 'text', 'note', 'on-disk', 'external']):
                    if 'id' in prototype[k]:
                        node[k] = prototype[k]
                    else:
                        node[k] = copy.copy(prototype[k]) # one level copy
        if uploaded_file:
            node['on-disk'] = uploaded_file
        paper._new_node(node)

        box.children = tuple([ edit_node(paper, node)])

    if upload:
        _set_upload(upload)
    else:
        _set_edit("New " + _type)

    return box    
        

def edit_node(paper, node_or_key):
    """
    Live editing of a node
    """
    if type(node_or_key) is str:
        node = paper[node_or_key]
    else:
        node = node_or_key

    box = widgets.VBox()

    header = widgets.HTML("<h2>%s</h2><p>%s</p>" % ( node['id'], node['type']))

    def make_box():
        children = list()
        children.append(header)

        missing_entries = list()
        for k in sorted(paper.get_type_relations()[node['type']].keys()):
            if not k in node:
                missing_entries.append(k)

        children.append(make_toolbox(missing_entries))

        for k in sorted(node.keys()):
            if not k in ['id','type']:
                children.append(make_slot(k))

        box.children = tuple(children)

    def make_slot(slot):

        entries = node[slot]
        is_list = True

        if type(entries) != list:
            entries = [ entries ]
            is_list = False

        rows = []
        for i in range(0,len(entries)):
            
            def delete_row(source):
                if type(node[slot]) == list:
                    del node[slot][source.idx]
                    must_delete = len(node[slot]) == 0
                    if len(node[slot]) == 1:
                        node[slot] = node[slot][0]
                else:
                    must_delete = True
                if must_delete:
                    del node[slot]
                make_box()

            def add_row(source):
                if type(node[slot]) != list:
                    node[slot] = [ node[slot] ]
                node[slot].insert(source.idx+1, 'New entry')
                make_box()

            def move_up(source):
                if source.idx != 0:
                    to_move = node[slot][source.idx]
                    del node[slot][source.idx]
                    node[slot].insert(source.idx-1, to_move)
                    make_box()
                
            def move_dn(source):
                if source.idx != len(entries) - 1:
                    to_move = node[slot][source.idx]
                    del node[slot][source.idx]
                    node[slot].insert(source.idx+1, to_move)
                    make_box()
            
            delbtn = widgets.Button(description="-", layout=widgets.Layout(width="30px"))
            delbtn.idx = i
            delbtn.on_click(delete_row)
            addbtn = widgets.Button(description="+", layout=widgets.Layout(width="30px"))
            addbtn.idx = i
            addbtn.on_click(add_row)
            upbtn = widgets.Button(description="↑", layout=widgets.Layout(width="30px"))
            upbtn.idx = i
            upbtn.on_click(move_up)
            dnbtn = widgets.Button(description="↓", layout=widgets.Layout(width="30px"))
            dnbtn.idx = i
            dnbtn.on_click(move_dn)

            
            def make_textarea():
                idx = i
                if type(entries[i]) == str or type(entries[i]) == str:
                    value = entries[i]
                else:
                    value = repr(entries[i])
                if len(value) < 50:
                    text = widgets.Text(description=slot,value=value)
                else:
                    text = widgets.Textarea(description=slot,value=value)

                def live_edit(source):
                    if is_list:
                        node[slot][idx] = text.value
                    else:
                        node[slot] = text.value
                
                text.on_trait_change(live_edit, 'value')
                return text

            all_types = paper.get_type_relations()[node['type']][slot]
            if all_types:
                # toggle
                toggle = widgets.ToggleButtons(options=['string'] + all_types)
                if type(entries[i]) == str:
                    toggle.value = 'string'
                    edit = make_textarea()
                elif type(entries[i]) == dict and 'type' in entries[i]:
                    _type = entries[i]['type']
                    toggle.value = _type
                    allothers = paper.get_nodes_by_type(_type)
                    others = []
                    for j in range(0,len(allothers)):
                        full_text = safe_unicode(allothers[j]['text']) if 'text' in allothers[j] else ""
                        others.append( ( "%s - %s" % (safe_unicode(allothers[j]['id']), full_text[:80]),
                                      safe_unicode(allothers[j]['id'])) )

                    dropdown = widgets.Dropdown(description=slot,
                                                options=[("<none selected>", "paper-none")] + sorted(others))
                    if 'id' in entries[i]:
                        dropdown.value = entries[i]['id']
                    else:
                        dropdown.value = 'paper-none'

                    def change_target(source):
                        if dropdown.value:
                            if dropdown.value == 'paper-none':
                                if is_list:
                                    node[slot][i] = ""
                                else:
                                    node[slot] = ""
                            else:
                                value = paper[dropdown.value]
                                if is_list:
                                    node[slot][i] = value
                                else:
                                    node[slot] = value

                    dropdown.on_trait_change(change_target, 'value')

                    search = widgets.Text(description="search",value="")
                    def live_search(source):
                        if search.value == "":
                            dropdown.options = sorted(others)
                        else:
                            new_options = []
                            
                            for j in range(0,len(allothers)):
                                obj = allothers[j]
                                found = False
                                for k,v in obj.items():
                                    if search.value.lower() in safe_unicode(k).lower() or \
                                      search.value.lower() in safe_unicode(v).lower():
                                        found = True
                                        break
                                if found:
                                    new_options.append(others[j])
                            dropdown.options = sorted(new_options)
                            
                    search.on_trait_change(live_search, 'value')            

                    edit = widgets.HBox(children=(dropdown, search))
                else:
                    toggle.value = 'string'
                    edit = make_textarea()

                def change_type(source):
                    if toggle.value == 'string':
                        value = 'New string'
                    else:
                        value = { 'type':toggle.value }
                    if is_list:
                        node[slot][i] = value
                    else:
                        node[slot] = value
                    make_box()

                toggle.on_trait_change(change_type, 'value')

                content = widgets.VBox(children=[ toggle, edit ])
            else:
                content = make_textarea()

            if is_list:
                rows.append(widgets.HBox(children=( addbtn, delbtn, upbtn, dnbtn, content )))
            else:
                rows.append(widgets.HBox(children=( addbtn, delbtn, content )))
            
        return widgets.VBox(children=tuple(rows))
        

    def make_toolbox(other_entries):
        refresh_btn = widgets.Button(description="Refresh")

        def do_refresh(source):
            make_box()
        refresh_btn.on_click(do_refresh)
        
        save_btn = widgets.Button(description="Save")
        def do_save(source):
            paper.auto_save()
            make_box()
        save_btn.on_click(do_save)
        
        select = widgets.Dropdown(description="Add a missing entry:",
                                  options=['(None)'] + other_entries,
                                  layout=widgets.Layout(width="50%"),
                                  style={'description_width': 'initial'})
        def add_new_entry(source):
            node[select.value] = 'New entry'
            make_box()
        select.on_trait_change(add_new_entry, 'value')
        return widgets.HBox(children=( refresh_btn, save_btn, select ))
    

    make_box()
    return box


class NodeEditor:
    def __init__(self):
        self.path = os.getcwd()
        self._update_files()
        
    def _update_files(self):
        self.files = list()
        self.dirs = list()
        if(os.path.isdir(self.path)):
            for f in os.listdir(self.path):
                ff = self.path + "/" + f
                if os.path.isdir(ff):
                    self.dirs.append(f)
                else:
                    self.files.append(f)
        
    def widget(self):
        box = widgets.VBox()
        self._update(box)
        return box
    
    def _update(self, box):
        
        def on_click(b):
            if b.description == '..':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            self._update_files()
            self._update(box)
        
        buttons = []
        if self.files:
            button = widgets.Button(description='..', background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in self.dirs:
            button = widgets.Button(description=f, background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in self.files:
            button = widgets.Button(description=f)
            button.on_click(on_click)
            buttons.append(button)
        box.children = tuple([widgets.HTML("<h2>%s</h2>" % (self.path,))] + buttons)


def render_nodes(paper, nodes):
    """
    Render a list of nodes
    """
    children = []
    for i in range(0,len(nodes)):
        children.append(widgets.HTML("<h2>%d</h2>"% (i,)))
        children.append(render_node(paper,nodes[i]))
    return widgets.Box(children=children)    

def render_readinglist(paper, list_id):
    """
    Render a reading list
    """
    children = []
    for i in range(0,len(paper[list_id]['artifacts'])):
        children.append(widgets.HTML("<h2>%d</h2>"% (i,)))
        children.append(render_node(paper,paper[list_id]['artifacts'][i]))
    return widgets.Box(children=children)    

def render_publication(pub):
    url = re.sub("&.*","",pub.url_scholarbib.replace(".bib",""))
    return widgets.HTML("""<h2>%s</h2>
    <p>Citations: %d - <a href="http://scholar.google.com%s">see in Google Scholar</a></p>
    <h3>%s</h3>
    <p>%s</p>
    <p>Paper: <a href="%s">%s</a></p>
    """ % (pub.bib['title'],pub.citedby, url, pub.bib['author'],pub.bib['abstract'],
           pub.bib['url'],pub.bib['url']))

def render_publications(publications):
    children = []
    for i in range(0,len(publications)):
        children.append(widgets.HTML("<h1>%d</h1>" % (i,)))
        children.append(render_publication(publications[i]))
    return widgets.Box(children=children)


class FileBrowser:
    def __init__(self, path=None):
        if type(path) is str:
            self.path = path
        else:
            self.path = os.getcwd()
        self._update_files()
        
    def _update_files(self):
        self.files = list()
        self.dirs = list()
        if(os.path.isdir(self.path)):
            for f in os.listdir(self.path):
                ff = self.path + "/" + f
                if os.path.isdir(ff):
                    self.dirs.append(f)
                else:
                    self.files.append(f)
        
    def widget(self):
        box = widgets.VBox()
        self._update(box)
        return box
    
    def _update(self, box):
        
        def on_click(b):
            if b.description == '..':
                self.path = os.path.split(self.path)[0]
            else:
                self.path = self.path + "/" + b.description
            self._update_files()
            self._update(box)
        
        buttons = []
        if self.files or self.dirs:
            button = widgets.Button(description='..', background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in sorted(self.dirs):
            button = widgets.Button(description=f, background_color='#d0d0ff')
            button.on_click(on_click)
            buttons.append(button)
        for f in sorted(self.files):
            button = widgets.Button(description=f)
            button.on_click(on_click)
            buttons.append(button)
        box.children = tuple([widgets.HTML("<h2>%s</h2>" % (self.path,))] + buttons)

