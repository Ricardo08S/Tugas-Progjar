import os
import json
import base64
from glob import glob


class FileInterface:
    def __init__(self):
        os.chdir('files/')

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload(self, params=[]):
        try:
            filename = params[0]
            encoded_content = params[1]
            if not filename or not encoded_content:
                return dict(status='ERROR', data='Parameter filename atau content tidak lengkap')

            decoded_content = base64.b64decode(encoded_content)
            with open(f"{filename}", 'wb+') as fp:
                fp.write(decoded_content)
            return dict(status='OK', data=f"File {filename} berhasil diupload")
        except IndexError:
            return dict(status='ERROR', data='Format UPLOAD: UPLOAD <nama_file> <base64_content>')
        except Exception as e:
            return dict(status='ERROR', data=f"Gagal upload file: {str(e)}")

    def delete(self, params=[]):
        try:
            filename = params[0]
            if not filename:
                return dict(status='ERROR', data='Parameter filename tidak lengkap')

            if os.path.exists(f"{filename}"):
                os.remove(f"{filename}")
                return dict(status='OK', data=f"File {filename} berhasil dihapus")
            else:
                return dict(status='ERROR', data=f"File {filename} tidak ditemukan")
        except IndexError:
            return dict(status='ERROR', data='Format DELETE: DELETE <nama_file>')
        except Exception as e:
            return dict(status='ERROR', data=f"Gagal menghapus file: {str(e)}")

if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))