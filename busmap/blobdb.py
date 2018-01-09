# -*- coding: utf-8 -*-

import hashlib
import os
import shutil
import pickle

class BlobHandle:

    def __init__(self, db, blobid):
        self.db = db
        self.blobid = blobid

    def to_filename(self):
        return self.db.data_path_for(self.blobid)

    def to_fileobj(self, binary=False):
        return open(self.to_filename(), 'rb' if binary else 'r')

    def __str__(self):
        return self.blobid


class BlobStore:

    def __init__(self, blobdb_dir):
        self.blobdb_dir = blobdb_dir
        self.masterdb = None
        self.masterdbfn = os.path.join(self.blobdb_dir, 'master.db')

    def hashof(self, strm):
        m = hashlib.sha1()
        while True:
            data = strm.read(1024*1024*64)
            if not data:
                break
            m.update(data)
        return m.hexdigest()

    def keydata_to_key(self, keydata):
        serkey_array = []
        ordered_keys = sorted(keydata.keys())
        if 'blob' in keydata:
            ordered_keys.remove('blob')
            ordered_keys.insert(0, 'blob')

        for key in ordered_keys:
            serkey_array.append(str(key))
            serkey_array.append(str(keydata[key]))
        serkey = ':'.join(serkey_array)
        return serkey

    def preload_db(self):
        if self.masterdb is None:
            self.masterdb = {}
            if os.path.exists(self.masterdbfn):
                with open(self.masterdbfn, 'rb') as f:
                    self.masterdb = pickle.load(f)

    def add_db_entry(self, keydata, blobid_or_blobhandle):
        self.preload_db()
        if isinstance(blobid_or_blobhandle, BlobHandle):
            blob_id = blobid_or_blobhandle.blobid
        else:
            blob_id = blobid_or_blobhandle

        self.masterdb[self.keydata_to_key(keydata)] = blob_id
        with open(self.masterdbfn, 'wb') as f:
            pickle.dump(self.masterdb, f)

    def get_db_entry(self, keydata):
        self.preload_db()
        return self.masterdb.get(self.keydata_to_key(keydata))

    def data_path_for(self, hashval):
        return os.path.join(self.blobdb_dir, hashval[0], hashval)

    def has_blob(self, hashval):
        return os.path.exists(self.data_path_for(hashval))

    def import_file(self, fn):
        with open(fn, 'rb') as f:
            blobid = self.hashof(f)
        if not self.has_blob(blobid):
            shutil.copyfile(fn, self.data_path_for(blobid))
        return BlobHandle(self, blobid)




