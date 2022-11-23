import time
import os
import re
import requests
from . import youtube
from . import googledrive
from . import mediafire
from .megacli import mega
from .utils import req_file_size,get_file_size,get_url_file_name,slugify,createID,makeSafeFilename

class Downloader(object):
    def __init__(self,destpath=''):
        self.filename = ''
        self.stoping = False
        self.destpath = destpath
        if self.destpath!='':
            isExist = os.path.exists(self.destpath)
            if not isExist:
                os.makedirs(self.destpath)
        self.id = createID(12)
        self.url = ''
        self.progressfunc = None
        self.args = None

    async def download_url(self,url='',progressfunc=None,args=None,proxies=None):
        self.url = url
        self.progressfunc = progressfunc
        self.args = args
        req = None
        if 'youtube' in url or 'youtu.be' in url:
                try:
                    data = await youtube.getVideoData(url)
                    if data:
                        url = data['url']
                        self.filename = slugify(data['name'])
                    else: return None
                except: return None
        elif 'mediafire' in url:
                try:
                    url = mediafire.get(url)
                except:return None
        elif 'drive.google' in url:
                try:
                    info = googledrive.get_info(url)
                    self.filename = slugify(info['file_name'])
                    url = info['file_url']
                except:return None
        elif 'mega.nz' in url:
                try:
                    mg = mega.Mega()
                    mdl = mg.login()
                    info = mdl.get_public_url_info(url)
                    await mdl.download_url(url,dest_path=self.destpath,dest_filename=self.destpath+info['name'],progressfunc=progressfunc,args=args)
                    return ''
                except Exception as ex:
                    return None
        if req is None:
           req = requests.get(url,allow_redirects=True,stream=True)
        return await self._process_download(url,req,progressfunc=progressfunc,args=args)

    async def _process_download(self,url,req,progressfunc=None,args=None):
        if req is None:return None
        if req.status_code == 200:
            file_size = req_file_size(req)
            file_name = get_url_file_name(url,req)
            if self.filename!='':
                file_name = self.filename
                self.filename = makeSafeFilename(file_name)
            else:
                file_name = makeSafeFilename(file_name)
                self.filename = file_name
            file_wr = open(self.destpath+file_name,'wb')
            chunk_por = 0
            chunkrandom = 100
            total = file_size
            time_start = time.time()
            time_total = 0
            size_per_second = 0
            clock_start = time.time()
            for chunk in req.iter_content(chunk_size = 1024):
                    if self.stoping:break
                    chunk_por += len(chunk)
                    size_per_second+=len(chunk)
                    tcurrent = time.time() - time_start
                    time_total += tcurrent
                    time_start = time.time()
                    if time_total>=1:
                        clock_time = (total - chunk_por) / (size_per_second)
                        if progressfunc:
                            await progressfunc(self,self.filename,chunk_por,total,size_per_second,clock_time,args)
                        time_total = 0
                        size_per_second = 0
                    file_wr.write(chunk)
            file_wr.close()
            return self.destpath+self.filename
        return None

    def stop(self):self.stoping=True
    def renove(self):
        self.download_url(self.url,self.progressfunc,self.args)
