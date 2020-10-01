import yaml
import os
import datetime
import random
import hashlib

from .             import PaperError
from .paper_yaml   import Dumper, safe_unicode
from .file_repo    import FileRepo
from .search_index import SearchIndex

# repo class
class PaperRepo:

    def __init__(self,
                 yaml_file=None,
                 file_folder=None,
                 index_folder=None,
                 data_folder=None,
                 auto_save=False,
                 custom_types=None):
        """Create a paper repository object. 

        With no options, an empty one with no file repository nor search
        index is created.

        If a yaml_file is provided, the auto_save option can be set to
        True. The object will then save itself after each change.

        If a file repository is desired, point file_folder to it or to
        an existing, empty folder to get started.

        If a serch index is desired, point index_folder to it or to an
        existing, empty folder to get started.

        Alternatively, a data_folder can be provided that will use
        ``paper-model.yaml`` as the yaml_file, ``files`` as the
        file_folder and ``index`` as the index_folder.

        Custom types can be provided, see get_default_types for the base
        types.
"""
        if data_folder:
            if not os.path.exists(data_folder):
                raise PaperError("Data folder must exist, got '{}'".format(data_folder))
            if not os.path.isdir(data_folder):
                raise PaperError("Data folder is not a folder, got '{}'".format(data_folder))
            yaml_file    = os.path.join(data_folder, "paper-model.yaml")
            file_folder  = os.path.join(data_folder, "files")
            index_folder = os.path.join(data_folder, "index")
            if not os.path.exists(file_folder):
                os.mkdir(file_folder)
            if not os.path.exists(index_folder):
                os.mkdir(index_folder)

        
        if yaml_file and os.path.exists(yaml_file):
            with open(yaml_file, "r") as yamlf:
                self.repo = yaml.load(yamlf, Loader=yaml.FullLoader)
            if self.repo[0]['type'] == 'types':
                self.types = self.repo[0]['types']
                del self.repo[0]
            else:
                self.types = PaperRepo.get_default_types()
        else:
            self.repo = []
            self.types = PaperRepo.get_default_types()
            
        if custom_types:
            custom_types = PaperRepo.add_default_entries(custom_types)
            self.types = custom_types

        self.file_hashes = {}
        self.verify()

        self.file_repo = FileRepo(file_folder) if file_folder else None
        if auto_save:
            self._auto_save = yaml_file
        else:
            self._auto_save = None

        self.search_index = SearchIndex(index_folder) if index_folder else None
        if self.search_index:
            if not self.file_repo:
                raise PaperError("Cannot have a search engine without a file repository.")
            all_files = self.get_nodes_by_type('file')
            if self.search_index.size() != len(all_files):
                print("Index contains {} documents, file repository contains {} files. Reindexing...".format(
                    self.search_index.size(), len(all_files)))
                self.search_index.refresh(all_files, self.file_repo)

        # defaults
        self.default_topic = None
        self.default_context = None # search or paper, used for 'found-in'

    def save(self, path_to_yaml):
        with open(path_to_yaml, 'w') as f:
            f.write(yaml.dump([ { 'type' : 'types', 'types' : self.types } ] + self.repo, Dumper=Dumper))

    def auto_save(self):
        if self._auto_save is not None:
            self.save(self._auto_save)

    def __getitem__(self, key):
        """Get a node by a given key, note that setitem is not defined as
        it involves a number of substeps and require the caller to know
        what they are doing."""
        return self.id_to_node[key]

    def __contains__(self, key):
        return key in self.id_to_node

    def verify(self):
        self.counts_by_type = {}
        self.maxid_by_type = {}
        for node in self.repo:
            if 'type' in node:
                node_type = node['type']
                self.counts_by_type[node_type] = self.counts_by_type.get(node_type, 0) + 1
                if 'id' in node and node['id'][0:len(node_type)+1] == node_type+"-":
                    try:
                        intid = int(node['id'][len(node_type)+1:])
                    except ValueError:
                        intid = 0
                    if not node_type in self.maxid_by_type:
                        self.maxid_by_type[node_type] = 0
                    self.maxid_by_type[node_type] = max(self.maxid_by_type[node_type], intid)

        self.id_to_node = {}
        for node in self.repo:
            if 'id' in node:
                node_id = node['id']
                if node_id in self.id_to_node:
                    raise PaperError("Duplicated id: '%s'" % node_id)
                self.id_to_node[node_id] = node
            else: # manufacture an id from type
                if 'type' in node:
                    node_type = node['type']
                    self.counts_by_type[node_type] += 1
                    self.maxid_by_type[node_type] += 1
                    c = self.maxid_by_type[node_type]  # start from 1
                    node_id = '%s-%d' % (node_type, c)
                    node['id'] = node_id
                    
                    self.id_to_node[node_id] = node
                else:
                    raise PaperError("No id and no type: '%s'" % yaml.dump(node))
                    
        for node in self.repo:
            for k,v in node.items():
                if type(v) == dict:
                    self.verify_node(k, v)

        # verify all nodes now have a type
        for node in self.repo:
            if not 'type' in node:
                raise PaperError("Node id '%s' has no type" % node['id'])
            self.verify_relations(node)

        # collect file hashes
        self.hashes = {}
        for node in self.repo:
            if node['type'] == 'file':
                if 'md5hash' in node:
                    md5hash = node['md5hash']
                else:
                    print("Using random hash for {}".format(node['id']))
                    l = list(map(str,range(1000)))
                    random.shuffle(l)
                    md5hash = hashlib.md5("".join(l).encode('utf-8')).hexdigest()
                    while md5hash in self.hashes:
                        random.shuffle(l)
                        md5hash = hashlib.md5("".join(l).encode('utf-8')).hexdigest()
                self.hashes[md5hash] = node['id']

        # compute hash
        return self.versionhash()

    def versionhash(self):
        def stablehash(obj):
            result = 0
            if type(obj) == str or type(obj) == str:
                for c in obj:
                    result += ord(c)
            if type(obj) == int or type(obj) == int:
                result += obj
            if type(obj) == float:
                result += int(obj)
            if type(obj) == list:
                i = 1
                for o in obj:
                    result += i * stablehash(o)
                    i += 7
            if type(obj) == dict:
                for k,v in obj.items():
                    result += stablehash(k) ^ stablehash(v)
            return result
        return stablehash(self.repo)

    def verify_node(self, k, node):
        """Verify the node has a type, an id and that it exists in the repo as a separate node"""
        in_repo = False
        if 'id' in node and node['id'] in self.id_to_node:
            in_repo = True
        else:
            # brute force check if is in the repo
            for other in self.repo:
                if other == node:
                    in_repo = True
                    break

        type_count = -1
        if not 'type' in node:
            node_type = k
            print("Assigning type '%s' to node '%s'" % (node_type, yaml.dump(node)))
            node['type'] = node_type
            self.counts_by_type[node_type] = self.counts_by_type.get(node_type, 0) + 1
            self.maxid_by_type[node_type] = self.maxid_by_type.get(node_type, 0) + 1 # just in case
            type_count = self.maxid_by_type[node_type] # start from 1
        else:
            node_type = node['type']
            if not in_repo:
                self.counts_by_type[node_type] = self.counts_by_type.get(node_type, 0) + 1
                self.maxid_by_type[node_type] = self.maxid_by_type.get(node_type, 0) + 1  # just in case
                type_count = self.maxid_by_type[node_type] # start from 1

        if not 'id' in node:
            node_id = '%s-%d' % (node_type, type_count)
            print("Assigning id '%s' to node '%s'" % (node_id, yaml.dump(node)))
            node['id'] = node_id
            self.id_to_node[node_id] = node
        else:
            node_id = node['id']

        if not in_repo:
            print("Adding node id '%s' to repo" % (node_id,))
            self.repo.append(node)

    DEFAULT_TYPES = None

    def get_type_relations(self):
        return self.types

    @classmethod
    def get_default_types(cls):
        """Base types used by the tool."""
        
        if cls.DEFAULT_TYPES is None:
            # { type: { key: list of target types (ORed, scalar is assumed) } }
            # all have 'type', 'id', 'text', 'note', 'date'
            cls.DEFAULT_TYPES = {
                'topic': { 'related-to': ['topic'] },
                'search': { 'site': [], 'date': [], 'related-to': ['topic'] },
                'artifact': { 'related-to': ['topic'],
                              'on-disk': ['file'],
                              'found-in' : ['search','artifact', 'external'],
                              'found-date' : [],
                              'bibtex': ['bibtex'],
                              'external' : ['external'],
                              'status' : [],
                              'read': ['scenario'],
                              },
                'bibtex' : {}, # dealt below
                'place'  : {},
                'file' : { 'md5hash': [], 'number': [], 'mimetype': [] },
                'scenario' : { 'location' : [ 'place' ] },
                'external' : { 'url' : [], 'cited-by' : [], 'provider' : [] },
                'reading-list' : { 'related-to' : [ 'topic' ], 'artifacts': [ 'artifact' ] },
                'relation' : { 'source' : [ 'artifact' ], 'target' : [ 'artifact' ] },
                }
            for v in [ 'booktitle', 'title', 'author', 'year', 'pages', 'organization', 'journal', 'publisher',
                       'number', 'volume', 'howpublished', 'institution', 'address', 'meta', 'school',
                       'biburl', 'timestamp', 'link', 'editor', 'month', 'crossref', 'chapter', 'isbn',
                       'series', 'doi', 'issue', 'issn' ]:
                cls.DEFAULT_TYPES['bibtex'][v] = []

            cls.add_default_entries(cls.DEFAULT_TYPES)
        return cls.DEFAULT_TYPES
    
    @classmethod
    def add_default_entries(cls, types):
        """Ensure all types have the default entries: 'type', 'id', 'text', 'note', 'date'.
        """
        for v in list(types.values()):
            for e in [ 'type', 'id', 'text', 'note', 'date' ]:
                v[e] = []
        return types
        
    
    def verify_relations(self, node):
        """
        Verify all the relations make sense for a given type.
        """
        for node in self.repo:
            _type = node['type']
            if not _type in self.types:
                raise PaperError('Type "%s" for node "%s" cannot be validated! Known types: %s' %
                                (_type, yaml.dump(node),
                                 ", ".join(list(self.types.keys()))))
            valid = self.types[_type]
            for k, v in node.items():
                if not k in valid:
                    raise PaperError('Key "%s" for node "%s" (of type "%s") is invalid! Valid keys: %s' %
                                    (k, yaml.dump(node), _type,
                                     ", ".join(list(valid.keys()))))
                if type(v) == dict:
                    target = v['type']
                    if not target in valid[k]:
                        raise PaperError('Value for key "%s" in node "%s" if of type "%s" which is invalid! Valid types are: %s' %
                                        (k, yaml.dump(node), target,
                                         ", ".join(valid[k])))

    def _resolve_list(self, list_or_elem, node, key):
        """
        Take a single element or a list of elements and resolve them to nodes.
        Set the single item directly on node or the list.
        If the list is None, node is unchanged
        """
        if list_or_elem is None:
            return

        if type(list_or_elem) == str:
            node[key] = self.id_to_node[list_or_elem]
        elif type(list_or_elem) == dict:
            node[key] = list_or_elem
        else:
            _list = []
            for e in list_or_elem:
                if type(e) == str:
                    _list.append(self.id_to_node[e])
                elif type(e) == dict:
                    _list.append(e)
                else:
                    raise PaperError("Unknown type: %s, %s" % (type(e), yaml.dump(list_or_elem)))
            if len(_list) > 0:
                 node[key] = _list

    def _new_node(self, node):
        _id   = node['id']
        _type = node['type']
        if _id in self.id_to_node:
            raise PaperError("Node with id '%s' already exists: %s" % (_id, yaml.dump(self.id_to_node[_id])))
        self.repo.append(node)
        self.id_to_node[_id] = node
        self.counts_by_type[_type] = self.counts_by_type.get(_type, 0) + 1
        if _id[0:len(_type)+1] == _type+"-":
            try:
                intid = int(_id[len(_type)+1:])
            except ValueError:
                intid = 0
            if not _type in self.maxid_by_type:
                self.maxid_by_type[_type] = 0
            self.maxid_by_type[_type] = max(self.maxid_by_type[_type], intid)

    def _delete_node(self, to_delete):
        pos_to_delete = list()
        for pos in range(0,len(self.repo)):
            node = self.repo[pos]
            if node == to_delete or node['id'] == to_delete['id']:
                pos_to_delete.append(pos)
            else:
                keys_to_delete = list()
                for k,v in node.items():
                    if type(v) == list:
                        pos_to_delete2 = list()
                        for i in range(0,len(v)):
                            if v[i] == to_delete or (type(v[i]) == dict and 'id' in v[i] and v[i]['id'] == to_delete['id']):
                                pos_to_delete2.append(i)
                        pos_to_delete2.reverse()
                        for i in pos_to_delete2:
                            del v[i]
                        if len(v) == 0:
                            keys_to_delete.append(k)
                    elif type(v) == dict:
                        keys_to_delete2 = list()
                        for k2,v2 in v.items():
                            if v2 == to_delete or (type(v2) == dict and 'id' in v2 and v2['id'] == to_delete['id']):
                                keys_to_delete2.append(v2)
                        for k2 in keys_to_delete2:
                            del v[k2]
                        if len(v) == 0:
                            keys_to_delete.append(k)
                    elif v == to_delete or (type(v) == dict and 'id' in v and v['id'] == to_delete['id']):
                        keys_to_delete.append(k)

                for k in keys_to_delete:
                    del node[k]
        pos_to_delete.reverse()
        for i in pos_to_delete:
            del self.repo[i]

        # recalculate counts and id_to_node
        self.verify()

    def _replace_node(self, to_delete, replacement):
        pos = 0
        pos_to_delete = list()
        for node in self.repo:
            if node == to_delete:
                pos_to_delete.append(pos)
            else:
                for k,v in node.items():
                    if type(v) == list:
                        for i in range(0,len(v)):
                            if v[i] == to_delete:
                                v[i] = replacement
                    elif type(v) == dict:
                        for k2,v2 in v.items():
                            if v2 == to_delete:
                                v[k2] = replacement
                    elif v == to_delete:
                        node[k] = v
            pos += 1
        pos_to_delete.reverse()
        for i in pos_to_delete:
            del self.repo[i]

        # recalculate counts and id_to_node
        self.verify()

    def _base_node(self, _id, _type, text=None, date=None, note=None):
        node = { 'id' : _id, 'type' : _type }
        if text is not None:
            node['text'] = text
        if date is not None:
            node['date'] = date
        if note is not None:
            node['note'] = note
        return node

    def _validate_id(self, _id, _type, suffix=None):
        if suffix is None:
            suffix = _type

        if _id is None or _id == "":
            _id = '%s-%d' % (suffix, self.maxid_by_type.get(_type, 0) + 1,)

        if _id in self.id_to_node:
            raise PaperError("Id '%s' already exists: %s" % (_id, yaml.dump(self.id_to_node[_id])))

        return _id
                    
    # CLI helpers
    def get_nodes_by_type(self, _type):
        return [node for node in self.repo if node['type'] == _type ]

    def get_nodes_on_topic(self, topic):
        if type(topic) == str:
            topic = self.id_to_node[topic]
        topic_id = topic['id']
        result = []
        for node in self.repo:
            if 'related-to' in node:
                topics = node['related-to']
                if type(topics) is dict:
                    if topics == topic:
                        result.append(node)
                elif topic_id in [ other['id'] for other in topics]:
                    result.append(node)
        return result

    def register_file(self, path_to_file):
        """
        Register the file and create a node for it.
        """
        if not os.path.exists(path_to_file):
            raise PaperError("File '%s' not found" % (path_to_file,))

        if not self.file_repo:
            raise PaperError("File repository not defined.")

        node_or_key = self.file_repo.register_file(path_to_file, self.hashes)
        if len(node_or_key) == 1:
            key = node_or_key['id']
            raise PaperError("File already registered, key: '%s'" % (key,))
        else:
            node = node_or_key
        if self.search_index:
            self.search_index.index_content(node['id'],
                                            self.file_repo.get_absolute_path_to_file(node['number']),
                                            node['mimetype'])
        
        self._new_node(node)
        self.hashes[node['md5hash']] = node['id']
        self.auto_save()
        
        return node

    def process_folder(self, path_to_folder):
        """
        All files in folder are registered and a list of nodes for them is returned.
        The files are deleted after registration.
        """
        if not os.path.exists(path_to_folder):
            raise PaperError("Folder '%s' not found" % (path_to_folder,))

        if not self.file_repo:
            raise PaperError("File repository not defined.")
        
        nodes_or_keys = self.file_repo.process_folder(path_to_folder)

        result = list()

        changed = False
        for node_or_key in nodes_or_keys:
            if len(node_or_key) == 1:
                key = node_or_key['id']
                node = self.id_to_node[key]
            else:
                node = node_or_key
                self.hashes[node['md5hash']] = node['id']                
                if self.search_index:
                    self.search_index.index_content(node['id'],
                                                    self.file_repo.get_absolute_path_to_file(node['number']),
                                                    node['mimetype'])
                self._new_node(node)
                changed = True
            result.append(node)
        if changed:
            self.auto_save()
        
        return result

    def delete_file(self, file_id):
        """
        Delete a given file_id, also from disk.
        """
        if self.file_repo:
            raise PaperError("File repository not defined.")

        del self.hashes[self.id_to_node[file_id]['md5hash']]
        self._delete_node(self.id_to_node[file_id])
        self.file_repo.delete_file(file_id)
        if self.search_index:
            self.search_index.delete(file_id)
        self.auto_save()
        
    def replace_file(self, file_id, path_to_file):
        """
        Delete a given file_id, also from disk, register a new file and change its references to it.
        """
        if self.file_repo:
            raise PaperError("File repository not defined.")
        
        replacement = self.register_file(path_to_file)
        self._replace_node(self.id_to_node[file_id], replacement)
        self.hashes[replacement['md5hash']] = replacement['id']
        
        self.file_repo.delete_file(file_id)
        if self.search_index:
            self.search_index.delete(file_id)
            self.search_index.index_content(replacement['id'],
                                            self.file_repo.get_absolute_path_to_file(replacement['number']),
                                            replacement['mimetype'])            
        self.auto_save()

        return replacement

    def similarto(self, fileid, limit=20, numterms=50):
        if fileid not in self.id_to_node:
            raise PaperError(filedid + " not found")
        node = self.id_to_node[fileid]
        if node['type'] == 'artifact':
            if 'on-disk' in node:
                node = node['on-disk']
        if node['type'] != 'file':
            raise PaperError("Node {} is not of type 'file'".format(node['id']))

        if not self.search_index:
            raise PaperError("Search index not initialized.")
        return self._enhance_results(self.search_index.similarto(node['id'], limit, numterms))

    def _enhance_results(self, results):
        all_papers = self.get_nodes_by_type('artifact')
        for idx, fileid in enumerate(results):
            paper = { 'id': "", 'text': "" }
            for node in all_papers:
                if 'on-disk' in node and ((type(node['on-disk']) is str and node['on-disk'] == fileid) or
                                              (type(node['on-disk']) is dict and node['on-disk']['id'] == fileid)):
                    paper = { 'id': node['id'], 'text': node.get('text', "") }
            results[idx] = { 'file'  : { 'id' : fileid, 'text' : self.id_to_node[fileid].get('text', "") }
                           , 'paper' : paper }
        return results
                
    def search(self, query_str, limit=20):
        if not self.search_index:
            raise PaperError("Search index not initialized.")
        return self._enhance_results(self.search_index.search(query_str, limit))

    def text(self, file_or_paperid):
        if file_or_paperid not in self.id_to_node:
            raise PaperError(file_or_paperid + " not found")
        node = self.id_to_node[file_or_paperid]
        if node['type'] == 'artifact':
            if 'on-disk' in node:
                node = node['on-disk']
        if node['type'] != 'file':
            raise PaperError("Node {} is not of type 'file'".format(node['id']))

        if not self.search_index:
            raise PaperError("Search index not initialized.")
        return self.search_index.text(node['id'])
    
    def set_default_topic(self, topic):
        """
        Set a session topic.
        """
        if type(topic) == str:
            topic = self.id_to_node[topic]
        self.default_topic = topic

    def set_default_context(self, search_or_paper):
        """
        Set a session context.
        """
        if search_or_paper is not None:
            if type(search_or_paper) == str:
                search_or_paper = self.id_to_node[search_or_paper]
            if not search_or_paper['type'] in ['search', 'artifact']:
                raise PaperError('Type "%s" can\'t be used as a context' % (search_or_paper['type']))
        self.default_context = search_or_paper

    # all these would be easier using **kwargs but I want to have the method signature to serve
    # as documentation for the users
    
    def new_node(self, _id, _type, text, date=None, note=None, **kwargs):
        """Create a new node of a given type. Returns the newly created node."""
        
        _id = self._validate_id(_id, _type)
        node = self._base_node(_id, _type, text, date, note)
        for key, value in kwargs.items():
            node[key] = value
        self._new_node(node)
        self.auto_save()
        return node

    
    def new_topic(self, _id, text, related_to=None, note=None, default=False):
        """
        Create a new topic, possibly related to existing ones.
        Returns the newly created node.
        """
        _id = self._validate_id(_id, 'topic')
        node = self._base_node(_id, 'topic', text)
        self._resolve_list(related_to, node, 'related-to')
        if note is not None:
            node['note'] = note
        self._new_node(node)
        self.auto_save()

        if default:
            self.set_default_topic(node)

        return node

    def new_external(self, _id, text, url=None, cited_by=None, provider=None):
        _id = self._validate_id(_id, 'external')
        node = self._base_node(_id, 'external', text)

        for k, v in { 'url' : url, 'cited-by' : cited_by, 'provider': provider }.items():
            if v is not None:
                node[k] = v

        self._new_node(node)
        self.auto_save()
        
        return node

    def new_search(self, _id, text, site=None, related_to=None, date=None, note=None, default=False):
        _id = self._validate_id(_id, 'search')
        node = self._base_node(_id, 'search', text)

        self._resolve_list(related_to, node, 'related-to')

        for k, v in { 'date' : date, 'note' : note, 'site': site }.items():
            if v is not None:
                node[k] = v

        self._new_node(node)
        self.auto_save()

        if default:
            self.set_default_context(node)

        return node

    def new_paper(self, _id, text, on_disk=None, related_to=None, found_in=None, found_date=None,
                  note=None, bibtex=None, external=None):
        if _id is None or _id == "":
            _id = 'paper-%d' % (self.counts_by_type.get('artifact', 0) + 1,)

        node = self._base_node(_id, 'artifact', text)
        for k, v in { 'on-disk' : on_disk, 'related-to' : related_to, 'found-in' : found_in, 'external' : external
                      }.items():
            self._resolve_list(v, node, k)

        for k, v in { 'found-date' : found_date, 'bibtex' : bibtex, 'note': note }.items():
            if v is not None:
                node[k] = v

        if related_to is None and self.default_topic is not None:
            node['related-to'] = self.default_topic

        if found_in is None and self.default_context is not None:
            node['found-in'] = self.default_context
            if found_date is None:
                now = datetime.datetime.now()
                node['found-date'] = "%d%d%d" % (now.year, now.month, now.day)

        self._new_node(node)
        self.auto_save()

        return node

    def new_reading_list(self, _id, text, *papers, **kwargs):
        """Create a new reading list, possibly related to some topics.

        Returns the newly created node. Valid keyword arguments are
        "related_to" and "note".
        """
        related_to=kwargs.pop('related_to', None)
        note=kwargs.pop('note', None)
        _id = self._validate_id(_id, 'reading-list')
        node = self._base_node(_id, 'reading-list', text)
        self._resolve_list(related_to, node, 'related-to')
        if note is not None:
            node['note'] = note

        node['artifacts'] = []
        self._resolve_list(papers, node, 'artifacts')
        self._new_node(node)
        self.auto_save()

        return node

    def add_to_reading_list(self, reading_list, paper, front=False):
        """
        Add a paper to the end of a reading list.
        Both can be expressed ids or nodes.
        Returns the reading list node
        """
        if type(reading_list) == str:
            reading_list = self.id_to_node[reading_list]
        if type(paper) == str:
            paper = self.id_to_node[paper]
        paper_id = paper['id']
        if not 'artifacts' in reading_list:
            reading_list['artifacts'] = []
        artifacts = reading_list['artifacts']
        # check is not already there
        if len([n for n in artifacts if n['id'] == paper_id]) == 0:
            if front:
                artifacts.insert(0, paper)
            else:
                artifacts.append(paper)
            self.auto_save()

        return reading_list

    def new_bibtex(self, _id, _type, meta, bibtexdict):
        """Create a bibtex entry"""

        entries_for_bibtex = self.types['bibtex']
        
        if _id is None or _id == "":
            _id = 'bibtex-%d' % (self.maxid_by_type.get('bibtex', 0) + 1,)
        node = self._base_node(_id, 'bibtex', _type)
        
        if meta:
            node['meta'] = meta
        
        for k,v in bibtexdict.items():
            if k in set(['ID', 'ENTRYTYPE']):
                continue
            if k in entries_for_bibtex:
                node[k] = v
            else:
                line = '(%s) %s' % (k,v)
                if 'meta' in node:
                    if type(node['meta']) == list:
                        node['meta'].append(line)
                    else:
                        node['meta'] = [ node['meta'], line ]
                else:
                    node['meta'] = line

        self._new_node(node)
        self.auto_save()
        return node

    def cite(self, paper, papers):
        """Create or add to a citing relation from one paper to others"""
        if type(paper) == str:
            paper = self.id_to_node[paper]
        if type(papers) == str:
            papers = self.id_to_node[papers]
        if type(papers) != list:
            papers = [ papers ]
        relation = None
        for r in self.get_nodes_by_type("relation"):
            if r['text'] == "citing":
                found = False
                if paper == r['source']:
                    found = True
                if type(r['source']) == list:
                    for x in r['source']:
                        if 'id' in x and x['id'] == paper[id]:
                            found = True
                            break
                if found:
                    relation = r
                    break
        if relation is None:
            relation = self._base_node(paper['id'] + "-citing", "relation", "citing")
            relation['source'] = paper
            relation['target'] = []
            self._new_node(relation)

        for other in papers:
            if type(other) == str:
                other = self.id_to_node[other]

            relation['target'].append(other)

        self.auto_save()
        return relation


# list of nodes with jquery style magic

class NodeList(list):

    def __init__(self, other):
        super(list, self).__init__(other)

    def setall(self,key,value):
        """set all the nodes entry to a given value"""
        for v in self:
            v[key] = value
    
    
