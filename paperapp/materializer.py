import os
import re
import codecs
import yaml
import mimetypes

from collections import defaultdict

from jinja2 import Environment, PackageLoader

from .paper_yaml import safe_unicode

def node_data(p, node, target=None, files_to_url=None):
    data=list()
    sorted_keys = sorted(node.keys())
    keys=[]
    for known in ['type','id','status','text','note','related-to']:
        if known in sorted_keys:
            keys.append(known)
            del sorted_keys[sorted_keys.index(known)]
    keys.extend(sorted_keys)
    for k in keys:
        entry = dict()
        entry['key'] = k
        v = node[k]
        if type(v) == str or type(v) == str:
            if node['type'] == 'file' and k == 'text':
                if files_to_url:
                    file_path = files_to_url[node['id']]
                else:
                    file_path = p.file_repo.get_absolute_path_to_file(node['id'])
                    if target:
                        file_path = os.path.relpath(file_path, target)
                entry['has_url'] = file_path
            else:
                entry['is_pre'] = True
            entry['value'] = safe_unicode(v)
        elif type(v) == list:
            entry['is_list'] = True
            entries = list()
            for vv in v:
                entry2 = dict()
                if type(vv) == str or type(vv) == str:
                    entry2['is_pre'] = True
                    entry2['value'] = safe_unicode(vv)
                elif type(vv) == dict:
                    entry2['has_url'] = vv['id'] + ".html"
                    value = vv['id']
                    if 'text' in vv:
                        value += " - " + safe_unicode(vv['text'])
                    entry2['value'] = value
                else:
                    entry2['is_pre'] = True
                    entry2['value'] = yaml.dump(vv)
                entries.append(entry2)
            entry['value'] = entries
        elif type(v) == dict and 'id' in v:
            entry['has_url'] = v['id'] + ".html"
            value = v['id']
            if 'text' in v:
                value += " - " + v['text']
            entry['value'] = safe_unicode(value)
        else:
            entry['is_pre'] = True
            entry['value'] = yaml.dump(v)
        data.append(entry)

    backlinks={} # key, set(target)
    for other in p.repo:
        for k,v in other.items():
            if not k in backlinks:
                backlinks[k] = set()
            if type(v) == list:
                for vv in v:
                    if type(vv) == dict and 'id' in vv and vv['id'] == node['id']:
                        backlinks[k].add(other['id'])
            elif type(v) == dict and 'id' in v and v['id'] == node['id']:
                backlinks[k].add(other['id'])
    backlinks_entries = list()
    for k in sorted(backlinks.keys()):
        v = backlinks[k]
        if len(v) > 0:
            entry = dict()
            entry['key'] = k
            nodes = list()
            for other_id in sorted(list(v)):
                vv = p.id_to_node[other_id]
                _node = { 'page' : vv['id'] + ".html" }
                text = vv['id']
                if 'text' in vv:
                    text += " - " + safe_unicode(vv['text'])
                _node['text'] = text
                nodes.append(_node)
            entry['nodes'] = nodes
            backlinks_entries.append(entry)

    # transitive closure for topic backlinks
    if node['type'] == 'topic':
        # compute descendants
        children = dict()
        for topic in p.get_nodes_by_type("topic"):
            children[topic['id']] = set([])
        for topic in p.get_nodes_by_type("topic"):
            if 'related-to' in topic:
                if type(topic['related-to']) == str:
                    children[topic['related-to']].add(topic['id'])
                elif type(topic['related-to']) == list:
                    for t in topic['related-to']:
                        children[t['related-to']['id']].add(topic['id'])
                else:
                    children[topic['related-to']['id']].add(topic['id'])
        prev_len = 0
        closure = children[ node['id'] ]
        while len(closure) > prev_len:
            prev_len = len(closure)
            for _id in list(closure):
                closure.update(children[_id])

        if closure:
            closure.add( node['id'] )
            backlinks={} # key, set(target)
            for other in p.repo:
                for k,v in other.items():
                    if not k in backlinks:
                        backlinks[k] = set()
                    if type(v) == list:
                        for vv in v:
                            if type(vv) == dict and 'id' in vv and vv['id'] in closure:
                                backlinks[k].add(other['id'])
                    elif type(v) == dict and 'id' in v and v['id'] in closure:
                        backlinks[k].add(other['id'])

            for k in sorted(backlinks.keys()):
                v = backlinks[k]
                if len(v) > 0:
                    entry = dict()
                    entry['key'] = "(closure) " + k
                    nodes = list()
                    for other_id in sorted(list(v)):
                        vv = p.id_to_node[other_id]
                        _node = { 'page' : vv['id'] + ".html" }
                        text = vv['id']
                        if 'text' in vv:
                            text += " - " + safe_unicode(vv['text'])
                        _node['text'] = text
                        nodes.append(_node)
                    entry['nodes'] = nodes
                    backlinks_entries.append(entry)
    return (data, backlinks_entries)
                            

# symlinks for topics reading lists
def materialize(p, target_path):
    """
    Materialize symlinks based on topics and reading lists.
    The target path should not exist.
    """
    if os.path.exists(target_path):
        raise Exception("Cannot materialize on path that already exists: '%s'" % (target_path,))

    mimetype_to_ext = defaultdict(lambda: '.bin')
    mimetype_to_ext.update( { t[1] : t[0] for t in mimetypes.types_map.items() } )
    mimetype_to_ext.update( { t[1] : t[0] for t in mimetypes.common_types.items() } )

    env = Environment(loader=PackageLoader('paperapp', 'templates'))

    os.mkdir(target_path)
    p.save(os.path.join(target_path,"paper-model.yaml"))

    # pages
    pages_path = os.path.join(target_path, "pages")
    template = env.get_template("node.html")
    os.mkdir(pages_path)
    files_path = os.path.join(pages_path, "files")
    os.mkdir(files_path)
    files_to_url={}
    for file_node in p.get_nodes_by_type('file'):
        fname = file_node['id'] + mimetype_to_ext[file_node['mimetype']]        
        os.symlink(os.path.relpath(p.file_repo.get_absolute_path_to_file(file_node['id']), files_path),
                   os.path.join(files_path, fname))
        files_to_url[file_node['id']] = "files/" + fname        
    for node in p.repo:
        # generate page
        (data, backlinks) = node_data(p, node, files_to_url=files_to_url)
        with codecs.open(os.path.join(pages_path, node['id'] + ".html"), 'w', 'utf-8') as f:
            f.write(template.render(_type=node['type'], _id=node['id'], data=data, backlinks=backlinks))

    # home page
    template = env.get_template("index.html")
    sorted_types = sorted(p.counts_by_type.keys())
    nodes=dict()
    for _type in sorted_types:
        nodes[_type] = list()
        for other in p.repo:
            if other['type'] == _type:
                node = dict()
                node['page'] = other['id'] + ".html"
                node['text'] = other['id']
                if 'text' in other:
                    node['text'] += " - " + safe_unicode(other['text'])
                nodes[_type].append(node)
        nodes[_type] = sorted(nodes[_type], key=lambda x:x['text'])
    
    with codecs.open(os.path.join(pages_path,"index.html"), 'w', 'utf-8') as f:
        f.write(template.render(_types=sorted_types, nodes=nodes))

    with codecs.open(os.path.join(target_path,"index.html"), 'w', 'utf-8') as f:
        f.write(template.render(_types=sorted_types, nodes=nodes, alter_base='pages/'))

    template = env.get_template("style.css")
    with codecs.open(os.path.join(pages_path,"style.css"), 'w', 'utf-8') as f:
        f.write(template.render())

    # file system
    for topic in p.get_nodes_by_type('topic'):
        topic_base = os.path.join(target_path, topic['id'])
        os.mkdir(topic_base)

        on_topic = p.get_nodes_on_topic(topic)

        # reading list
        reading_lists_on_topic = [ node for node in on_topic if node['type'] == 'reading-list' ]
        for _list in reading_lists_on_topic:
            reading_list = os.path.join(topic_base, _list['id'])
            os.mkdir(reading_list)

            papers = _list['artifacts']

            for i in range(0, len(papers)):
                paper = papers[i]
                if 'on-disk' in paper and type(paper['on-disk']) is dict:
                    paper_num = '%d' % (i+1)
                    if len(papers) > 10 and len(paper_num) == 1:
                        paper_num = '0' + paper_num
                    os.symlink(os.path.relpath(p.file_repo.get_absolute_path_to_file(paper['on-disk']['id']), reading_list),
                               (os.path.join(reading_list,
                                             '%s-%s-%s%s' % (_list['id'],
                                                               paper_num, paper['id'], mimetype_to_ext[paper['on-disk']['mimetype']]))))

        # all papers
        if len(reading_lists_on_topic) == 0:
            all_papers = topic_base
        else:
            all_papers = os.path.join(topic_base, 'all_papers')
            os.mkdir(all_papers)
        papers_on_topic = [ node for node in on_topic if node['type'] == 'artifact' ]
        for paper in papers_on_topic:
            if 'on-disk' in paper and type(paper['on-disk']) is dict:
                file_name = paper['id']
                if 'status' in paper:
                    status = re.sub('[^a-z]', '-', paper['status'].lower())
                    file_name = '%s-%s' % (status, file_name)
                os.symlink(os.path.relpath(p.file_repo.get_absolute_path_to_file(paper['on-disk']['id']), all_papers),
                           (os.path.join(all_papers, file_name + mimetype_to_ext[paper['on-disk']['mimetype']])))

