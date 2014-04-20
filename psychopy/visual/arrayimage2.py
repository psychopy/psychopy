# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2007-2008 Andrew Straw
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

#
# Updated Nov, 2013 by Sol Simpson:
#   * Added rectangle, force_rectangle kwargs to ArrayInterfaceImage
#     which are passed to pyglet when the opengl texture is created.
#

from pyglet.image import ImageData
import ctypes

__version__ = '1.0' # keep in sync with ../setup.py
__all__ = ['ArrayInterfaceImage']

def is_c_contiguous(inter):
    strides = inter.get('strides')
    shape = inter.get('shape')
    if strides is None:
        return True
    else:
        test_strides = strides[-1]
        N = len(strides)
        for i in range(N-2):
            test_strides *= test_strides * shape[N-i-1]
            if test_strides == strides[N-i-2]:
                continue
            else:
                return False
        return True

def get_stride0(inter):
    strides = inter.get('strides')
    if strides is not None:
        return strides[0]
    else:
        # C contiguous
        shape = inter.get('shape')
        cumproduct = 1
        for i in range(1,len(shape)):
            cumproduct *= shape[i]
        return cumproduct

class ArrayInterfaceImage(ImageData):
    def __init__(self,arr,format=None,allow_copy=True, rectangle=False, force_rectangle=False):
        '''Initialize image data from the numpy array interface

        :Parameters:
            `arr` : array
                data supporting the __array_interface__ protocol. If
                rank 2, the shape must be (height, width). If rank 3,
                the shape is (height, width, depth). Typestr must be
                '|u1' (uint8).
            `format` : str or None
                If specified, a format string describing the data
                format array (e.g. 'L', 'RGB', or 'RGBA'). Defaults to
                a format determined from the shape of the array.
            `allow_copy` : bool
                If False, no copies of the data will be made, possibly
                resulting in exceptions being raised if the data is
                unsuitable. In particular, the data must be C
                contiguous in this case. If True (default), the data
                may be copied to avoid such exceptions.

        '''

        self.inter = arr.__array_interface__
        self.allow_copy = allow_copy
        self.data_ptr = ctypes.c_void_p()
        self.data_ptr.value = 0

        self.rectangle=rectangle
        self.force_rectangle=force_rectangle
        
        if len(self.inter['shape'])==2:
            height,width = self.inter['shape']
            if format is None:
                format = 'L'
        elif len(self.inter['shape'])==3:
            height,width,depth = self.inter['shape']
            if format is None:
                if depth==3:
                    format = 'RGB'
                elif depth==4:
                    format = 'RGBA'
                elif depth==1:
                    format = 'L'
                else:
                    raise ValueError("could not determine a format for "
                                     "depth %d"%depth)
        else:
            raise ValueError("arr must have 2 or 3 dimensions")
        data = None
        pitch = get_stride0(self.inter)
        super(ArrayInterfaceImage, self).__init__(
            width, height, format, data, pitch=pitch)

        self.view_new_array( arr )

    def get_data(self):
        if self._real_string_data is not None:
            return self._real_string_data

        if not self.allow_copy:
            raise ValueError("cannot get a view of the data without "
                             "allowing copy")

        # create a copy of the data in a Python str
        shape = self.inter['shape']
        nbytes = 1
        for i in range(len(shape)):
            nbytes *= shape[i]
        mydata = ctypes.create_string_buffer( nbytes )
        ctypes.memmove( mydata, self.data_ptr, nbytes)
        return mydata.value

    data = property(get_data,None,"string view of data")

    def _convert(self, format, pitch):
        if format == self._current_format and pitch == self._current_pitch:
            # do something with these values to convert to a ctypes.c_void_p
            if self._real_string_data is None:
                return self.data_ptr
            else:
                # XXX pyglet may copy this to create a pointer to the buffer?
                return self._real_string_data
        else:
            if self.allow_copy:
                raise NotImplementedError("XXX")
            else:
                raise ValueError("cannot convert to desired "
                                 "format/pitch without copying")

    def _ensure_string_data(self):
        if self.allow_copy:
            raise NotImplementedError("XXX")
        else:
            raise ValueError("cannot create string data without copying")

    def dirty(self):
        '''Force an update of the texture data.
        '''

        texture = self.get_texture(rectangle=self.rectangle,
                                   force_rectangle=self.force_rectangle
                                  )
                                          
        internalformat = None
        self.blit_to_texture(
            texture.target, texture.level, 0, 0, 0, internalformat )

    def view_new_array(self,arr):
        '''View a new array of the same shape.

        The same texture will be kept, but the data from the new array
        will be loaded.

        :Parameters:
            `arr` : array
                data supporting the __array_interface__ protocol. If
                rank 2, the shape must be (height, width). If rank 3,
                the shape is (height, width, depth). Typestr must be
                '|u1' (uint8).
        '''

        inter = arr.__array_interface__

        if not is_c_contiguous(inter):
            if self.allow_copy:
                # Currently require numpy to deal with this
                # case. POSSIBLY TODO: re-implement copying into
                # string buffer so that numpy is not required.
                import numpy
                arr = numpy.array( arr, copy=True, order='C' )
                inter = arr.__array_interface__
            else:
                raise ValueError('copying is not allowed but data is not '
                                 'C contiguous')

        if inter['typestr'] != '|u1':
            raise ValueError("data is not type uint8 (typestr=='|u1')")

        if inter['shape'] != self.inter['shape']:
            raise ValueError("shape changed!")

        self._real_string_data = None
        self.data_ptr.value = 0

        idata = inter['data']
        if isinstance(idata,tuple):
            data_ptr_int,readonly = idata
            self.data_ptr.value = data_ptr_int
        elif isinstance(idata,str):
            self._real_string_data = idata
        else:
            raise ValueError("__array_interface__ data attribute was not "
                             "tuple or string")

        # maintain references so they're not de-allocated
        self.inter = inter
        self.arr = arr

        self.dirty()
