from psychopy import data

x=[0.1,0.2,0.3,0.4,0.5, 0.6]
y=[0.1,0.2,0.5,0.7,0.9,0.8]

myFunc = data.FitCumNormal(xx=x,yy=y, expectedMin=0)
#myFunc2 = data.FitFunction('logistYN',xx=x,yy=y)
print myFunc.eval(x)
print myFunc.params
print myFunc.inverse(myFunc.eval(x))

"""
[ 0.09031101  0.26949287  0.46916508  0.64717069  0.78403421  0.87766973]
[ 0.1  0.2  0.3  0.4  0.5  0.6]"""