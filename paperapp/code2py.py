

import sys
import re

def process_lines(lines, related_to=None, citing=None, file_folder='.', render=False):

    def output_current(current):
            res = []
            note = current.get('note', '').strip().replace("\\", "\\\\")
            num = current['num']
            res.append('# {}'.format(num))
            if len(note)> 0 and note[-1] == '"':
                  note = note + "\n"
            res.append('note="""{}"""'.format(note))
            res.append("\n")
            p = 'p{}'.format(num)
            res.append("{} = p.new_paper(None, {}, note=note {})".format(p, current['text'], ", related_to=p['{}']".format(related_to) if related_to else ""))
            res.append("{}['date'] = '{}'".format(p, current['text'][-7:-3]))
            res.append("{}['status'] = {}".format(p, current['status']))
            for k in [ 'on-disk', 'read', 'found-in', 'found-date', 'external', 'bibtex' ]:
                  if k in current:
                        res.append("{}['{}'] = {}".format(p, k, current[k]))
            if ('bibtex' in current) and citing:
                  res.append("p['{}']['target'].append({})".format(citing, p))
            if render:
                  res.append("render_node(p,{})\n\n\n\n".format(p))
            return res

    res = []
    current = dict()
    for line in lines:
        line = line.strip()
        if re.match("^p\d+", line):
            num = int(line[1:])
            if 'num' in current and num != current['num']+1:
                res.append("Expected {}, got {}".format(current['num']+1, num))
            if 'num' in current:
                res += output_current(current)
            current = { 'num': num }
        elif line[:2] == "E ":
            current['external'] = '"{}"'.format(line[2:])
        elif line[:2] == "O ":
            if line.startswith("O file-"):
                f = line.split(" ")[1]
                current['on-disk'] = 'p["{}"]'.format(f)
            else:
                current['on-disk'] = 'p.register_file(os.path.join("{}", "{}"))'.format(file_folder, line[2:])
        elif line[:2] == "T ":
            current['text'] = '"""{}"""'.format(line[2:])
        elif line[:2] == "S ":
            current['status'] = '"{}"'.format(line[2:])
        elif line[:2] == "R ":
            if 'read' in current:
                read = current['read']
                if read[-1:] == ']':
                    read = read[:-1]
                else:
                    read = "[" + read
                read = read + ', "{}"]'.format(line[2:])
                current['read'] = read
            else:
                current['read'] = '"{}"'.format(line[2:])
        elif line[:2] == "B ":
            current['bibtex'] = 'p["{}"]'.format(line[2:])
        elif line[:2] == "F ":
            line = line[2:]
            if line.startswith("201"):
                spc = line.index(" ")
                current['found-date'] = '"{}"'.format(line[:spc])
                line = line[(spc+1):]
            if re.match("^p\d+", line):
                current['found-in'] = line
            else:
                if '"' in line:
                    current['found-in'] = '""" {} """'.format(line)
                else:
                    current['found-in'] = '"{}"'.format(line)
        else:
            current['note'] = current.get('note', '') + "\n" + line

    return res + output_current(current)
