import hashlib
import shutil
import datetime
import os
import io

import pypandoc
import pdftotext
import textract

from magic import detect_from_content

from whoosh import index
from whoosh.filedb.filestore import FileStorage
from whoosh.fields   import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.qparser  import QueryParser


# search index
class SearchIndex:
    def __init__(self, index_folder):
        self.storage = FileStorage(index_folder)

        if not self.storage.index_exists():
            schema = Schema(fileid=ID(stored=True),
                            content=TEXT(stored=True))
            self.storage.create_index(schema)
        self.index = self.storage.open_index()

    def size(self):
        return self.index.doc_count()

    def list_files(self):
        with self.index.reader() as reader:
            for docnum, doc in reader.iter_docs():
                yield doc['fileid']

    def index_content(self, fileid, path_to_file, mimetype):
        """Index one file.
        """
        with self.index.writer() as writer:
            self._index_content(fileid, path_to_file, mimetype, writer)
        
    def delete(self, fileid):
        """Delete one file.
        """
        with self.index.searcher() as searcher:
            docnum = searcher.document_number(fileid=fileid)
        with self.index.writer() as writer:
            writer.delete_document(docnum)
        
    def _index_content(self, fileid, path_to_file, mimetype, writer):
        """Index one file.
        """
        if not mimetype in EXTRACTORS:
            content="Missing extractor for {}".format(mimetype)
        else:
            with open(path_to_file, 'rb') as f:
                document_bytes = f.read()
            magic = detect_from_content(document_bytes)
            
            content = EXTRACTORS[mimetype](path_to_file, document_bytes, magic)
        writer.add_document(fileid=fileid, content=content)
        
    def refresh(self, all_files, file_repo):
        """Extract the text from all the files in the repository, purging existing repo."""
        with self.index.reader() as reader:
            docids = list(reader.all_doc_ids())
        with self.index.writer() as writer:
            for docid in docids:
                writer.delete_document(docid)

            for node in all_files:
                self._index_content(node['id'],
                                    file_repo.get_absolute_path_to_file(node['number']),
                                    node['mimetype'],
                                    writer)

    def similarto(self, fileid, top=20, numterms=50):
        with self.index.searcher() as searcher:
            docnum = searcher.document_number(fileid=fileid)
            results = searcher.more_like(docnum, 'content', top=top, numterms=numterms, normalize=False)
            return list(map(lambda hit:hit['fileid'], results))
                
    def search(self, query_str, limit=20):
        qp = QueryParser('content', schema=self.index.schema)
        query = qp.parse(query_str)
        
        with self.index.searcher() as searcher:
            results = searcher.search(query, limit=limit)
            return list(map(lambda hit:hit['fileid'], results))

    def text(self, fileid):
        with self.index.searcher() as searcher:
            doc = searcher.document(fileid=fileid)
            if doc:
                return doc['content']
            else:
                return "File {} not in index!".format(fileid)

def text_only_wrapper(text):
    if type(text) is not str:
        if type(text) is bytes:
            try:
                s = text.decode('utf-8')
            except:
                s = str(text)
            text = s
        else:
            text = str(text)
    return text

def pandoc_wrapper(input_format):
    return lambda filename, content, magic: text_only_wrapper(pypandoc.convert_file(filename, 'plain', format=input_format))

def pdf_extractor(filename, content, magic):
    return text_only_wrapper("\n\n".join(pdftotext.PDF(io.BytesIO(content))))

def textractor_wrapper(extension):
    return lambda filename, content, magic: text_only_wrapper(textract.process(filename, extension=extension))

def text_extractor(filename, content, magic):
    return text_only_wrapper(str(content, encoding=magic.encoding))
        
EXTRACTORS = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': pandoc_wrapper("docx"),
    'application/msword': textractor_wrapper('doc'),
    'application/pdf': pdf_extractor,
    'application/vnd.oasis.opendocument.text': textractor_wrapper('odt'),
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': textractor_wrapper('pptx'),
    'application/vnd.ms-powerpoint': textractor_wrapper('ppt'),
    'text/rtf': textractor_wrapper('rtf'),
    'application/postscript': textractor_wrapper('ps'),
    'application/vnd.ms-excel': textractor_wrapper('xls'),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': textractor_wrapper('xlsx'),
    'text/html': textractor_wrapper('html'),
    'text/xml': textractor_wrapper('html'),
    'text/plain': text_extractor
}

