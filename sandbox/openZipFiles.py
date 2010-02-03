import zipfile, cStringIO, urllib2, socket, sys, os
import psychopy
socket.setdefaulttimeout(10)

class Updater:
    def __init__(self, app=None, proxy=None, runningVersion=psychopy.__version__):
        self.app=app
        self.runningVersion=runningVersion
        self.headers = {'User-Agent' : 'Mozilla/5.0'}
        
        self.setupProxies(proxy)
        #check for updates
        self.latest=self.checkForUpdates()
        if self.latest['version']>self.runningVersion:
            msg = "PsychoPy v%s is available (you are running %s). " %(self.latest['version'], self.runningVersion)
            msg+= "For details see full changelog at\nhttp://www.psychopy.org/changelog.html"
            msg+= "\n\nDo you want to update?\n\nYes = install\nCancel = not now\nNo = skip this version"
            print msg
        else:
            print "PsychoPy v%s is available (you are running %s). " %(self.latest['version'], self.runningVersion)
        
        self.fetchPsychoPy(v='latest')
        
    def setupProxies(self, proxy):
        """Get proxies and insert into url opener"""
        if proxy is None: proxies = urllib2.getproxies()
        else: proxies={'http':proxy}
        opener  = urllib2.build_opener(
            urllib2.ProxyHandler(proxies))
        urllib2.install_opener(opener)        
    def checkForUpdates(self):
        #open page
        URL = "http://www.psychopy.org/version.txt"
        page = urllib2.urlopen(URL)#proxies
        #parse that as a dictionary
        latest={}
        for line in page.readlines():
            key, keyInfo = line.split(':')
            latest[key]=keyInfo.replace('\n', '')
        return latest
    def fetchPsychoPy(self, v='latest'):
        if v=='latest':
            v=self.latest['version']
        
        #open page
        URL = "http://psychopy.googlecode.com/files/PsychoPy-%s.zip" %(v)
        URL = 'http://downloads.egenix.com/python/locale-0.1.zip'
        page = urllib2.urlopen(URL)
        #download in chunks so that we can monitor progress and abort mid-way through
        chunk=4096; read = 0
        fileSize = int(page.info()['Content-Length'])
        buffer=cStringIO.StringIO()
        while read<fileSize:
            buffer.write(page.read(chunk))
            read+=chunk
            print '.',; sys.stdout.flush()
        print 'download complete'
        page.close()
        zfile = zipfile.ZipFile(buffer)
        buffer.close()
        return zfile
    def installZipFile(self, zfile):
        currPath=self.app.prefs.paths[psychopy]
        rootPath,endPath=sys.path.split(currPath)
        #depending on install method, needs diff handling
        #if path ends with 'psychopy' then move it to 'psychopy-version' and create a new 'psychopy' folder for new version
        if endPath=='psychopy':#e.g. the mac standalone app
#            os.rename(currPath, "%s-%s" %(currPath, psychopy.__version__))
            os.mkdir(currPath+'X')
            unzipTarget=currPath+'X'
        
        zfile.extractall(unzipTarget)
        print 'installed to %s' %unzipTarget
def unzip_file_into_dir(file, dir):
    os.mkdir(dir, 0777)
    zfobj = zipfile.ZipFile(file)
    for name in zfobj.namelist():
        if name.endswith('/'):
            os.mkdir(os.path.join(dir, name))
        else:
            outfile = open(os.path.join(dir, name), 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

#up = Updater()
#up.fetchPsychoPy()

#print 'here1'
#URL = 'http://www.psychology.nottingham.ac.uk/staff/jwp/teaching/c81MST.zip'
#URL = 'http://www.psychopy.org/test.zip'
#URL = "https://psychopy.googlecode.com/files/PsychoPy-1.51.00.zip"
#headers={
#    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
#    'Accept-Language': 'en-us',
#    'Accept-Encoding': 'gzip, deflate, compress;q=0.9',
#    'Keep-Alive': '300',
#    'Connection': 'keep-alive',
#    'Cache-Control': 'max-age=0',
#    }
#req = urllib2.Request(URL, None, headers)
#response = urllib2.urlopen(req)
#page  = urllib2.urlopen(URL)
#print page.info()
#zfile = zipfile.ZipFile(cStringIO.StringIO(page.read()))
#print zfile.printdir()
