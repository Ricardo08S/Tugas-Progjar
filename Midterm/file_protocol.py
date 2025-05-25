import json
import logging
# import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""


class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    def proses_string(self,string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk}")
        
        parts = string_datamasuk.split(' ', 2) 
        
        try:
            c_request = parts[0].strip().lower()
            
            params = []
            if len(parts) > 1:
                params.append(parts[1])
            if len(parts) > 2:
                params.append(parts[2])
            
            logging.warning(f"memproses request: {c_request} dengan params: {params}")
            cl = getattr(self.file,c_request)(params)
            return json.dumps(cl)
        except AttributeError:
            return json.dumps(dict(status='ERROR', data='request tidak dikenali'))
        except IndexError:
            return json.dumps(dict(status='ERROR', data='Parameter tidak lengkap untuk request ini'))
        except Exception as e:
            return json.dumps(dict(status='ERROR',data=f'Kesalahan pemrosesan: {str(e)}'))


if __name__=='__main__':
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))