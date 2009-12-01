import zipfile, cStringIO, urllib2, socket
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
        print 'here'
        if v=='latest':
            v=self.latest['version']
        
        #open page
        URL = "http://psychopy.googlecode.com/files/PsychoPy-%s.zip" %(v)
        URL = 'http://downloads.egenix.com/python/locale-0.1.zip'
        page = urllib2.urlopen(URL)
        print 'here2'
        zfile = zipfile.ZipFile(cStringIO.StringIO(page.read()))
        print zfile.printdir()

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
print 'here1'
URL = 'http://www.psychology.nottingham.ac.uk/staff/jwp/teaching/c81MST.zip'
URL = 'http://www.psychopy.org/test.zip'
URL = "http://psychopy.googlecode.com/files/PsychoPy-1.51.01-py2.5.egg"
headers={
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
    'Accept-Language': 'en-us',
    'Accept-Encoding': 'gzip, deflate, compress;q=0.9',
    'Keep-Alive': '300',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    }
req = urllib2.Request(URL, None, headers)
response = urllib2.urlopen(req)
page  = urllib2.urlopen(URL)
zfile = zipfile.ZipFile(cStringIO.StringIO(page.read()))
print zfile.printdir()
