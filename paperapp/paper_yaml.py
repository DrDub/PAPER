import yaml

from yaml.emitter import *
from yaml.serializer import *
from yaml.representer import *
from yaml.resolver import *


# for pretty printing the aliases
class Dumper(Emitter, Serializer, Representer, Resolver):

    def __init__(self, stream,
            default_style=None, default_flow_style=None,
            canonical=None, indent=None, width=None,
            allow_unicode=None, line_break=None,
            encoding=None, explicit_start=None, explicit_end=None,
            version=None, tags=None, sort_keys=True):
        Emitter.__init__(self, stream, canonical=canonical,
                indent=indent, width=width,
                allow_unicode=allow_unicode, line_break=line_break)
        Serializer.__init__(self, encoding=encoding,
                explicit_start=explicit_start, explicit_end=explicit_end,
                version=version, tags=tags)
        Representer.__init__(self, default_style=default_style,
                default_flow_style=default_flow_style, sort_keys=sort_keys)
        Resolver.__init__(self)

    def generate_anchor(self, node):
        if isinstance(node, yaml.nodes.MappingNode):
            found_id = None
            for v in node.value:
                if v[0].value == 'id':
                    found_id = v[1].value
                    break
            if found_id:
                return found_id

        return Serializer.generate_anchor(self, node)

def safe_unicode(obj, encoding='utf-8'):
    if isinstance(obj, str):
        if not isinstance(obj, str):
            obj = str(obj, encoding)
        return obj
    return str(obj.__repr__())

