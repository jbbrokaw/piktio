import boto
from binascii import a2b_base64
import threading

def _upload(key_id, datastring):
    # Boto connections are not thread safe,
    # and getting one is potentially blocking,
    # so we create a new one for each thread
    # TODO: Handle boto errors
    # Probably need to do these conn tasks
    # in try/except blocks since failure is
    # inevitable.
    s3 = boto.connect_s3()
    bucket = s3.get_bucket('pikts.piktio.com')
    k = boto.s3.key.Key(bucket)
    k.key = key_id
    k.set_contents_from_string(datastring)

def upload_photo(key_id, data_url):
    """Encode & upload (nonblocking) a data url to S3"""
    datastring = data_url.split(',')[1]
    datastring = a2b_base64(datastring)
    threading.Thread(
        target=_upload,
        args=(key_id, datastring)
    ).start()
