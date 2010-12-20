import monitors

thisMon = monitors.Monitor('sparrow')
lPre = thisMon.getLumsPre()[0]
rPre = thisMon.getLumsPre()[1]
gPre = thisMon.getLumsPre()[2]
bPre = thisMon.getLumsPre()[3]

lPost = thisMon.getLumsPost()[0]
rPost = thisMon.getLumsPost()[1]
gPost = thisMon.getLumsPost()[2]
bPost = thisMon.getLumsPost()[3]
for n in range(len(thisMon.getLevelsPre())):
    print thisMon.getLevelsPre()[n], rPre[n], gPre[n], bPre[n], lPre[n]

print ''

for n in range(len(thisMon.getLevelsPost())):
    print thisMon.getLevelsPost()[n], rPost[n], gPost[n], bPost[n], lPost[n]
    
#thisMon.getLumsPre
#thisMon.getLevelsPost()
#thisMon.getLumsPost