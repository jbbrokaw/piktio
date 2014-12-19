import boto
from binascii import a2b_base64
import threading


def upload_photo(key_id, picture_string):
    s3 = boto.connect_s3()
    bucket = s3.get_bucket('pikts.piktio.com')
    k = boto.s3.key.Key(bucket)
    k.key = key_id
    datastring = picture_string.split(',')[1]
    datastring = a2b_base64(datastring)
    threading.Thread(target=k.set_contents_from_string, args=(datastring,))\
        .start()
