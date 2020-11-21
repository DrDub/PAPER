import hashlib
import shutil
import datetime
import os
import stat

from magic import detect_from_content


# file repo
class FileRepo:

    def __init__(self, path_to_file_folder):
        if not os.path.isdir(path_to_file_folder):
            raise Exception("Folder with files repository not found: '%s'" % (path_to_file_folder,))
        self.file_folder = path_to_file_folder

    def register_file(self, path_to_file, hashes):
        """
        Register a file and returns a dictionary with the following keys:
           type: file
           id: file-<file id>
           date: current date in format yyyy/mm/dd
           text: original file name
        (if the file already exists, only the id is returned, not a dictionary)
        A copy of the file is placed inside the repository.
        The original file is left intact.
        This method computes the MD5 hash for file so it won't store duplicates.
        If the file already exists, its ID is returned.
        """
        analysis = self._analyze_file(path_to_file)
        md5hash  = analysis['md5hash']
        existing = hashes.get(md5hash)
        if existing:
            return { 'id' : existing }

        inv_hashes = { t[1]: t[0] for t in hashes.items() }

        new_id = 0
        file_id = 'file-%d' % (new_id,)
        while file_id in inv_hashes:
            new_id += 1
            file_id = 'file-%d' % (new_id,)

        # copy it
        dest_file = os.path.join(self.file_folder, self._number_to_file(new_id))
        shutil.copy(path_to_file, dest_file)
        hashes[md5hash] = file_id

        # set read-only
        os.chmod(dest_file, stat.S_IREAD|stat.S_IRGRP|stat.S_IROTH)
        
        now = datetime.datetime.now()
        result = analysis
        analysis.update({
            'id'      : file_id,
            'type'    : 'file',
            'date'    : "%d%02d%02d" % (now.year, now.month, now.day),
            'number'  : new_id,
            })
        return result

    def process_folder(self, path_to_folder, hashes):
        """
        All files in folder are registered and a list of dictionaries as returned by register_file is returned.
        The files are deleted after registration.
        """
        # only process files in the folder, no subfolders
        _, _, files = next(os.walk(path_to_folder))

        result = []
        for _file in files:
            _full_file = os.path.join(path_to_folder, _file)
            result.append(self.register_file(_full_file, hashes))
            os.unlink(_full_file)

        return result

    def _number_to_file(self, file_id):
        file_id_as_str = str(file_id)
        while len(file_id_as_str) < 4:
            file_id_as_str = "0" + file_id_as_str

        chars = [c for c in file_id_as_str]
        _file = None
        for i in range(0, 3):
            if _file is None:
                _file = str(chars.pop())
            else:
                _file = os.path.join(_file, chars.pop())
            _dir = os.path.join(self.file_folder, _file)
            if not os.path.isdir(_dir):
                os.mkdir(_dir)

        chars.reverse()
        
        return os.path.join(_file, "".join(chars))

    def _number_from_id(self, file_id):
        FILE = 'file-'
        FILELEN = len(FILE)
        if type(file_id) == str:
            if file_id[0:FILELEN] == FILE:
                file_id = int(file_id[FILELEN:])
            else:
                file_id = int(file_id)
        return file_id

    def get_absolute_path_to_file(self, file_id_or_number):
        """
        Get an absolute path to a given file.
        This method also verifies the actual entry exists.
        """
        if type(file_id_or_number) is int:
            file_number = file_id_or_number
        else:
            file_number = self._number_from_id(file_id_or_number)
        file_path = os.path.join(self.file_folder, self._number_to_file(file_number))

        if not os.path.exists(file_path):
            raise Exception("File not found '%d'" % (file_number,))

        return file_path

    def delete_file(self, file_id_or_number):
        """
        Delete a file_id. This method throws an exception if the file does not exist.
        """
        if type(file_id_or_number) is int:
            file_number = file_id_or_number
        else:
            file_number = self._number_from_id(file_id_or_number)

        os.unlink(os.path.join(self.file_folder, self._number_to_file(file_id)))
        return file_number
        
    def analyze_file(self, file_id_or_number):
        """Recalculates the hash and mimetype for a file in the repo.
        """
        if type(file_id_or_number) is int:
            file_number = file_id_or_number
        else:
            file_number = self._number_from_id(file_id_or_number)

        path_to_file = os.path.join(self.file_folder, self._number_to_file(file_number))
        result = self._analyze_file(path_to_file)
        result.update({
            'number' : file_number
            })
        return result
                     
    def _analyze_file(self, path_to_file):
        content   = open(path_to_file, 'rb').read()
        md5hash   = hashlib.md5(content).hexdigest()
        magic     = detect_from_content(content)
        filetype  = magic.mime_type
        orig_name = os.path.basename(path_to_file)
        _, orig_ext  = os.path.splitext(orig_name)
        if filetype == 'application/octet-stream' and magic.name == 'Microsoft OOXML':
            if orig_ext == '.pptx':
                filetype = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif orig_ext == '.docx':
                filetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif orig_ext == '.xlsx':
                filetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  
        return { 'md5hash' : md5hash,
                 'mimetype': filetype,
                 'text'    : orig_name
               }
