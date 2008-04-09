#include <WINDOWS.H> // winbase.h is all we really want, but it doesn't include all the headers it needs
#include <WINBASE.H>
#include "Python.h"



/********************************************
windows specific functions
********************************************/
static PyObject *
win32_setProcessPriority( int priority_class ) {
  unsigned short retval;
  retval = (unsigned short)SetPriorityClass( GetCurrentProcess(), priority_class );
  return (PyObject*)Py_BuildValue("i",retval);
}

static PyObject *
win32_setThreadPriority( int priority ) {
  unsigned short retval;
  retval = (unsigned short)SetThreadPriority( GetCurrentThread(), priority );
  return (PyObject*)Py_BuildValue("i",retval);
}


//Always need a PyMethodDef and an initModule
static PyMethodDef
win32Methods[] = {
	{"setProcessPriority", win32_setProcessPriority, METH_VARARGS },
	{"setThreadPriority",win32_setThreadPriority, METH_VARARGS },
	{NULL, NULL},//this just marks the end of the list
};

void init_win32(){
	Py_InitModule("_win32",win32Methods);
}