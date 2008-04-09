#include <stdio.h>
#include "Python.h"
//#include "arrayobject.h"
#include <bits.h>


/********************************************
functions to control bits
********************************************/
static PyObject *
bits_init(PyObject *self, PyObject *args) {
    if (bitsInit("")<0)
        return NULL;
    else
    	return (PyObject*)Py_BuildValue("i",1);
}

static PyObject *
bits_setVideoMode(PyObject *self, PyObject *args) {
    PyObject *videoMode;
    if (!PyArg_ParseTuple(args, "i",	&videoMode))
        return NULL;	
    if (bitsSetVideoMode(videoMode)) 
        return NULL;
    else 
    	return  (PyObject*)Py_BuildValue("i",1);
}

//Always need a PyMethodDef and an initModule
static PyMethodDef
bitsMethods[] = {
    {"bitsInit",bits_init,METH_VARARGS},
    {"bitsSetVideoMode",bits_setVideoMode,METH_VARARGS},
    //{"bitsSlowSetLUT",bits_slowSetLUT,METH_VARARGS},
    {NULL, NULL},//this just marks the end of the list
};

void init_bits(){
    Py_InitModule("_bits",bitsMethods);
    //import_array() //this initialises numarray extension
}