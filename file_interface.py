import os
import json
import base64
from glob import glob


class FileInterface:
    def __init__(self):
        self.files_dir = 'files'
        os.makedirs(self.files_dir, exist_ok=True)

    def list(self,params=[]):
        try:
            filelist = [os.path.basename(f) for f in glob(os.path.join(self.files_dir, '*.*'))]
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return dict(status='ERROR', data='No Filename provided')
            filepath = os.path.join(self.files_dir, filename)
            with open(filepath, 'rb') as fp:
                isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload(self, params=[]):
        try:
            filename = ''
            content_b64 = ''
            for p in params:
                if p.startswith('filename='):
                    filename = p.split('=', 1)[1]
                elif p.startswith('content='):
                    content_b64 = p.split('=', 1)[1]
            if not filename or not content_b64:
                return dict(status='ERROR', data='Missing filename or content')
            filepath = os.path.join(self.files_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(content_b64))
            return dict(status='OK', data=f'Uploaded {filename}')
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def delete(self, params=[]):
        try:
            filename = ''
            for p in params:
                if p.startswith('filename='):
                    filename = p.split('=', 1)[1]
            if not filename:
                return dict(status='ERROR', data='Missing filename')
            filepath = os.path.join(self.files_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return dict(status='OK', data=f'Deleted {filename}')
            else:
                return dict(status='ERROR', data='File not found')
        except Exception as e:
            return dict(status='ERROR', data=str(e))




if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))
    
    # Test upload
    print(f.upload(['filename=halo.txt', 'content=aGVsbG8gd29ybGQ=']))

    # Test delete
    print(f.delete(['filename=halo.txt']))
