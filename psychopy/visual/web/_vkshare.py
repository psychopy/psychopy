#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Allocating GPU memory and semaphores both processes can import.

OpenGL can import memory and semaphores from other APIs, but can't allocate
them for export itself, so the web browser server allocates them with Vulkan
(which is otherwise unused) and passes them to its OpenGL context and to the
stimulus' as handles: file descriptors on Linux, NT handles on Windows. Only
the few Vulkan calls this needs are bound, with ctypes.

This module only uses the standard library, as the server imports it without
importing PsychoPy.
"""

import ctypes
import ctypes.util
import sys

__all__ = ['VulkanError', 'VulkanAllocator', 'listDevices']

_VK_SUCCESS = 0
_API_VERSION_1_1 = (1 << 22) | (1 << 12)

_ST_APPLICATION_INFO = 0
_ST_INSTANCE_CREATE_INFO = 1
_ST_DEVICE_QUEUE_CREATE_INFO = 2
_ST_DEVICE_CREATE_INFO = 3
_ST_MEMORY_ALLOCATE_INFO = 5
_ST_SEMAPHORE_CREATE_INFO = 9
_ST_IMAGE_CREATE_INFO = 14
_ST_PHYSICAL_DEVICE_PROPERTIES_2 = 1000059001
_ST_PHYSICAL_DEVICE_ID_PROPERTIES = 1000071004
_ST_EXTERNAL_MEMORY_IMAGE_CREATE_INFO = 1000072001
_ST_EXPORT_MEMORY_ALLOCATE_INFO = 1000072002
_ST_EXPORT_SEMAPHORE_CREATE_INFO = 1000077000
_ST_MEMORY_GET_WIN32_HANDLE_INFO_KHR = 1000073003
_ST_MEMORY_GET_FD_INFO_KHR = 1000074002
_ST_SEMAPHORE_GET_WIN32_HANDLE_INFO_KHR = 1000078003
_ST_SEMAPHORE_GET_FD_INFO_KHR = 1000079001
_ST_MEMORY_DEDICATED_ALLOCATE_INFO = 1000127001

_WINDOWS = sys.platform == 'win32'
if _WINDOWS:
    import _winapi
# what memory and semaphores are exported as: NT handles on Windows, file
# descriptors elsewhere, with the extensions and functions for each
if _WINDOWS:
    _HANDLE_TYPE = 0x2  # VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_WIN32_BIT
    _DEVICE_EXTENSIONS = (
        b'VK_KHR_external_memory_win32', b'VK_KHR_external_semaphore_win32')
    _GET_MEMORY = (b'vkGetMemoryWin32HandleKHR',
                   _ST_MEMORY_GET_WIN32_HANDLE_INFO_KHR)
    _GET_SEMAPHORE = (b'vkGetSemaphoreWin32HandleKHR',
                      _ST_SEMAPHORE_GET_WIN32_HANDLE_INFO_KHR)
    _OSHandle = ctypes.c_void_p  # HANDLE
    _FUNCTYPE = ctypes.WINFUNCTYPE
else:
    _HANDLE_TYPE = 0x1  # VK_EXTERNAL_MEMORY_HANDLE_TYPE_OPAQUE_FD_BIT
    _DEVICE_EXTENSIONS = (
        b'VK_KHR_external_memory_fd', b'VK_KHR_external_semaphore_fd')
    _GET_MEMORY = (b'vkGetMemoryFdKHR', _ST_MEMORY_GET_FD_INFO_KHR)
    _GET_SEMAPHORE = (b'vkGetSemaphoreFdKHR', _ST_SEMAPHORE_GET_FD_INFO_KHR)
    _OSHandle = ctypes.c_int
    _FUNCTYPE = ctypes.CFUNCTYPE

_FORMAT_R8G8B8A8_UNORM = 37
_IMAGE_TYPE_2D = 1
_SAMPLE_COUNT_1 = 1
_TILING_OPTIMAL = 0
# transfer source and destination, sampled, color attachment
_IMAGE_USAGE = 0x1 | 0x2 | 0x4 | 0x10
_MEMORY_DEVICE_LOCAL = 0x1

_u32 = ctypes.c_uint32
_u64 = ctypes.c_uint64
_i32 = ctypes.c_int32
_p = ctypes.c_void_p
_P = ctypes.POINTER
_handle = ctypes.c_void_p  # dispatchable handles (instance, device, ...)
_nhandle = ctypes.c_uint64  # non-dispatchable handles (image, memory, ...)


class _ApplicationInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p),
                ('pApplicationName', ctypes.c_char_p),
                ('applicationVersion', _u32), ('pEngineName', ctypes.c_char_p),
                ('engineVersion', _u32), ('apiVersion', _u32)]


class _InstanceCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('flags', _u32),
                ('pApplicationInfo', ctypes.POINTER(_ApplicationInfo)),
                ('enabledLayerCount', _u32), ('ppEnabledLayerNames', _p),
                ('enabledExtensionCount', _u32),
                ('ppEnabledExtensionNames', _p)]


class _DeviceQueueCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('flags', _u32),
                ('queueFamilyIndex', _u32), ('queueCount', _u32),
                ('pQueuePriorities', ctypes.POINTER(ctypes.c_float))]


class _DeviceCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('flags', _u32),
                ('queueCreateInfoCount', _u32),
                ('pQueueCreateInfos', ctypes.POINTER(_DeviceQueueCreateInfo)),
                ('enabledLayerCount', _u32), ('ppEnabledLayerNames', _p),
                ('enabledExtensionCount', _u32),
                ('ppEnabledExtensionNames', ctypes.POINTER(ctypes.c_char_p)),
                ('pEnabledFeatures', _p)]


class _PhysicalDeviceIDProperties(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p),
                ('deviceUUID', ctypes.c_ubyte * 16),
                ('driverUUID', ctypes.c_ubyte * 16),
                ('deviceLUID', ctypes.c_ubyte * 8),
                ('deviceNodeMask', _u32), ('deviceLUIDValid', _u32)]


class _PhysicalDeviceProperties2(ctypes.Structure):
    # the properties themselves (~830 bytes) are only read for the name, at
    # offset 20 (after apiVersion, driverVersion, vendorID, deviceID, type)
    _fields_ = [('sType', _u32), ('pNext', _p),
                ('properties', ctypes.c_ubyte * 2048)]


class _Extent3D(ctypes.Structure):
    _fields_ = [('width', _u32), ('height', _u32), ('depth', _u32)]


class _ImageCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('flags', _u32),
                ('imageType', _u32), ('format', _u32), ('extent', _Extent3D),
                ('mipLevels', _u32), ('arrayLayers', _u32), ('samples', _u32),
                ('tiling', _u32), ('usage', _u32), ('sharingMode', _u32),
                ('queueFamilyIndexCount', _u32), ('pQueueFamilyIndices', _p),
                ('initialLayout', _u32)]


class _ExternalMemoryImageCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('handleTypes', _u32)]


class _MemoryRequirements(ctypes.Structure):
    _fields_ = [('size', _u64), ('alignment', _u64), ('memoryTypeBits', _u32)]


class _MemoryType(ctypes.Structure):
    _fields_ = [('propertyFlags', _u32), ('heapIndex', _u32)]


class _MemoryHeap(ctypes.Structure):
    _fields_ = [('size', _u64), ('flags', _u32)]


class _PhysicalDeviceMemoryProperties(ctypes.Structure):
    _fields_ = [('memoryTypeCount', _u32), ('memoryTypes', _MemoryType * 32),
                ('memoryHeapCount', _u32), ('memoryHeaps', _MemoryHeap * 16)]


class _MemoryDedicatedAllocateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('image', _nhandle),
                ('buffer', _nhandle)]


class _ExportMemoryAllocateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('handleTypes', _u32)]


class _MemoryAllocateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('allocationSize', _u64),
                ('memoryTypeIndex', _u32)]


class _GetHandleInfo(ctypes.Structure):
    # VkMemoryGetFdInfoKHR, VkSemaphoreGetFdInfoKHR and their Win32 versions:
    # the memory or semaphore, and the type of handle to get for it
    _fields_ = [('sType', _u32), ('pNext', _p), ('object', _nhandle),
                ('handleType', _u32)]


class _ExportSemaphoreCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('handleTypes', _u32)]


class _SemaphoreCreateInfo(ctypes.Structure):
    _fields_ = [('sType', _u32), ('pNext', _p), ('flags', _u32)]


class VulkanError(RuntimeError):
    """Vulkan isn't available, or can't allocate memory to share."""


def _check(result, what):
    if result != _VK_SUCCESS:
        raise VulkanError("{} failed (VkResult {})".format(what, result))


def _loadVulkan():
    try:
        if _WINDOWS:
            return ctypes.WinDLL('vulkan-1')
        if sys.platform.startswith('linux'):
            return ctypes.CDLL(
                ctypes.util.find_library('vulkan') or 'libvulkan.so.1')
    except OSError as err:
        raise VulkanError("No Vulkan loader ({})".format(err))
    raise VulkanError(
        "Sharing frames on the GPU is only done on Linux and Windows")


class _Exportable:
    """Memory or a semaphore, which handles can be exported for."""
    def __init__(self, allocator):
        self._allocator = allocator
        self._ntHandle = None

    def _newHandle(self, getHandle, infoType, obj):
        if not _WINDOWS:
            return self._allocator._export(getHandle, infoType, obj)
        # an NT handle can only be exported once for each object, so that one
        # is kept and copies of it given
        if self._ntHandle is None:
            self._ntHandle = self._allocator._export(getHandle, infoType, obj)
        process = _winapi.GetCurrentProcess()
        return _winapi.DuplicateHandle(process, self._ntHandle, process, 0,
                                       False, _winapi.DUPLICATE_SAME_ACCESS)

    def _closeHandle(self):
        if self._ntHandle is not None:
            _winapi.CloseHandle(self._ntHandle)
            self._ntHandle = None


class SharedImage(_Exportable):
    """GPU memory for one frame, allocated for export.

    Attributes
    ----------
    width, height : int
        Size in pixels (RGBA, 8 bits per channel, optimal tiling).
    size : int
        Size of the memory in bytes, needed to import it.

    """
    def __init__(self, allocator, image, memory, width, height, size):
        super().__init__(allocator)
        self.image = image
        self.memory = memory
        self.width = width
        self.height = height
        self.size = size

    def exportHandle(self):
        """Get a new handle for the memory (a file descriptor, or an NT handle
        on Windows), which the caller owns."""
        return self._newHandle(
            self._allocator._getMemoryHandle, _GET_MEMORY[1], self.memory)

    def destroy(self):
        self._closeHandle()
        if self.memory is not None:
            self._allocator._destroyImage(self.image, self.memory)
            self.image = self.memory = None


class SharedSemaphore(_Exportable):
    """A semaphore, created for export."""
    def __init__(self, allocator, semaphore):
        super().__init__(allocator)
        self.semaphore = semaphore

    def exportHandle(self):
        """Get a new handle for the semaphore (a file descriptor, or an NT
        handle on Windows), which the caller owns."""
        return self._newHandle(
            self._allocator._getSemaphoreHandle, _GET_SEMAPHORE[1],
            self.semaphore)

    def destroy(self):
        self._closeHandle()
        if self.semaphore is not None:
            self._allocator._destroySemaphore(self.semaphore)
            self.semaphore = None


class VulkanAllocator:
    """Allocates exportable memory and semaphores on one GPU.

    Parameters
    ----------
    deviceUUID, driverUUID : str
        UUIDs (hex) of the GPU and driver the OpenGL contexts importing them
        run on, as `_glext.GLFunctions.uuids()` gives them. Memory can only be
        shared between contexts on the same device and driver.

    Raises
    ------
    VulkanError
        If Vulkan isn't available, has no matching device, or the device can't
        export memory and semaphores as handles.

    """
    def __init__(self, deviceUUID, driverUUID):
        self._vk = _loadVulkan()
        self._instance = None
        self._device = None
        self._bind()
        self._createInstance()
        if deviceUUID is None:  # only listing devices, see `listDevices`
            return
        try:
            self._physical, self.deviceName = self._findDevice(
                deviceUUID, driverUUID)
            self._createDevice()
            memProps = _PhysicalDeviceMemoryProperties()
            self._vk.vkGetPhysicalDeviceMemoryProperties(
                self._physical, ctypes.byref(memProps))
            self._memProps = memProps
            argtypes = (_handle, _P(_GetHandleInfo), _P(_OSHandle))
            self._getMemoryHandle = self._deviceProc(
                _GET_MEMORY[0], _i32, argtypes)
            self._getSemaphoreHandle = self._deviceProc(
                _GET_SEMAPHORE[0], _i32, argtypes)
        except Exception:
            self.destroy()
            raise

    def _bind(self):
        vk = self._vk
        sigs = {
            'vkCreateInstance': (
                _i32, (_P(_InstanceCreateInfo), _p, _P(_handle))),
            'vkDestroyInstance': (None, (_handle, _p)),
            'vkEnumeratePhysicalDevices': (
                _i32, (_handle, _P(_u32), _P(_handle))),
            'vkGetPhysicalDeviceProperties2': (
                None, (_handle, _P(_PhysicalDeviceProperties2))),
            'vkGetPhysicalDeviceMemoryProperties': (
                None, (_handle, _P(_PhysicalDeviceMemoryProperties))),
            'vkCreateDevice': (
                _i32, (_handle, _P(_DeviceCreateInfo), _p, _P(_handle))),
            'vkDestroyDevice': (None, (_handle, _p)),
            'vkGetDeviceProcAddr': (_p, (_handle, ctypes.c_char_p)),
            'vkCreateImage': (
                _i32, (_handle, _P(_ImageCreateInfo), _p, _P(_nhandle))),
            'vkDestroyImage': (None, (_handle, _nhandle, _p)),
            'vkGetImageMemoryRequirements': (
                None, (_handle, _nhandle, _P(_MemoryRequirements))),
            'vkAllocateMemory': (
                _i32, (_handle, _P(_MemoryAllocateInfo), _p, _P(_nhandle))),
            'vkFreeMemory': (None, (_handle, _nhandle, _p)),
            'vkBindImageMemory': (_i32, (_handle, _nhandle, _nhandle, _u64)),
            'vkCreateSemaphore': (
                _i32, (_handle, _P(_SemaphoreCreateInfo), _p, _P(_nhandle))),
            'vkDestroySemaphore': (None, (_handle, _nhandle, _p)),
        }
        for name, (restype, argtypes) in sigs.items():
            try:
                func = getattr(vk, name)
            except AttributeError:
                raise VulkanError("Vulkan loader has no {}".format(name))
            func.restype = restype
            func.argtypes = argtypes

    def _deviceProc(self, name, restype, argtypes):
        address = self._vk.vkGetDeviceProcAddr(self._device, name)
        if not address:
            raise VulkanError("Device has no {}".format(name.decode()))
        return _FUNCTYPE(restype, *argtypes)(address)

    def _createInstance(self):
        app = _ApplicationInfo(
            _ST_APPLICATION_INFO, None, b'PsychoPy web', 1, b'PsychoPy', 1,
            _API_VERSION_1_1)
        info = _InstanceCreateInfo(
            _ST_INSTANCE_CREATE_INFO, None, 0, ctypes.pointer(app), 0, None, 0,
            None)
        instance = _handle()
        _check(self._vk.vkCreateInstance(
            ctypes.byref(info), None, ctypes.byref(instance)),
            'vkCreateInstance')
        self._instance = instance

    def _devices(self):
        """Each physical device, with its name and UUIDs."""
        count = _u32(0)
        _check(self._vk.vkEnumeratePhysicalDevices(
            self._instance, ctypes.byref(count), None),
            'vkEnumeratePhysicalDevices')
        devices = (_handle * count.value)()
        _check(self._vk.vkEnumeratePhysicalDevices(
            self._instance, ctypes.byref(count), devices),
            'vkEnumeratePhysicalDevices')
        found = []
        for device in devices:
            ids = _PhysicalDeviceIDProperties(
                _ST_PHYSICAL_DEVICE_ID_PROPERTIES, None)
            props = _PhysicalDeviceProperties2(
                _ST_PHYSICAL_DEVICE_PROPERTIES_2,
                ctypes.cast(ctypes.pointer(ids), _p))
            self._vk.vkGetPhysicalDeviceProperties2(device, ctypes.byref(props))
            name = bytes(props.properties[20:276]).split(b'\0', 1)[0].decode(
                'utf-8', 'replace')
            uuids = (bytes(ids.deviceUUID).hex(), bytes(ids.driverUUID).hex())
            found.append((device, name, uuids))
        return found

    def _findDevice(self, deviceUUID, driverUUID):
        found = self._devices()
        for device, name, uuids in found:
            if uuids == (deviceUUID, driverUUID):
                return device, name
        found = [(name, uuids) for device, name, uuids in found]
        raise VulkanError(
            "No Vulkan device matches the OpenGL one ({}, {}), found {}".format(
                deviceUUID, driverUUID, found))

    def _createDevice(self):
        priority = ctypes.c_float(1.0)
        queue = _DeviceQueueCreateInfo(
            _ST_DEVICE_QUEUE_CREATE_INFO, None, 0, 0, 1,
            ctypes.pointer(priority))
        names = (ctypes.c_char_p * len(_DEVICE_EXTENSIONS))(*_DEVICE_EXTENSIONS)
        info = _DeviceCreateInfo(
            _ST_DEVICE_CREATE_INFO, None, 0, 1, ctypes.pointer(queue), 0, None,
            len(_DEVICE_EXTENSIONS), names, None)
        device = _handle()
        _check(self._vk.vkCreateDevice(
            self._physical, ctypes.byref(info), None, ctypes.byref(device)),
            'vkCreateDevice')
        self._device = device

    def _memoryType(self, typeBits):
        props = self._memProps
        for i in range(props.memoryTypeCount):
            if typeBits & (1 << i) and \
                    props.memoryTypes[i].propertyFlags & _MEMORY_DEVICE_LOCAL:
                return i
        raise VulkanError("No device-local memory type for the image")

    def allocateImage(self, width, height):
        """Allocate memory for an RGBA image, for export.

        Parameters
        ----------
        width, height : int
            Size of the image in pixels.

        Returns
        -------
        SharedImage

        """
        external = _ExternalMemoryImageCreateInfo(
            _ST_EXTERNAL_MEMORY_IMAGE_CREATE_INFO, None, _HANDLE_TYPE)
        info = _ImageCreateInfo(
            _ST_IMAGE_CREATE_INFO, ctypes.cast(ctypes.pointer(external), _p), 0,
            _IMAGE_TYPE_2D, _FORMAT_R8G8B8A8_UNORM,
            _Extent3D(int(width), int(height), 1), 1, 1, _SAMPLE_COUNT_1,
            _TILING_OPTIMAL, _IMAGE_USAGE, 0, 0, None, 0)
        image = _nhandle()
        _check(self._vk.vkCreateImage(
            self._device, ctypes.byref(info), None, ctypes.byref(image)),
            'vkCreateImage')
        try:
            reqs = _MemoryRequirements()
            self._vk.vkGetImageMemoryRequirements(
                self._device, image, ctypes.byref(reqs))
            dedicated = _MemoryDedicatedAllocateInfo(
                _ST_MEMORY_DEDICATED_ALLOCATE_INFO, None, image, 0)
            export = _ExportMemoryAllocateInfo(
                _ST_EXPORT_MEMORY_ALLOCATE_INFO,
                ctypes.cast(ctypes.pointer(dedicated), _p), _HANDLE_TYPE)
            alloc = _MemoryAllocateInfo(
                _ST_MEMORY_ALLOCATE_INFO,
                ctypes.cast(ctypes.pointer(export), _p), reqs.size,
                self._memoryType(reqs.memoryTypeBits))
            memory = _nhandle()
            _check(self._vk.vkAllocateMemory(
                self._device, ctypes.byref(alloc), None, ctypes.byref(memory)),
                'vkAllocateMemory')
            _check(self._vk.vkBindImageMemory(self._device, image, memory, 0),
                   'vkBindImageMemory')
        except Exception:
            self._vk.vkDestroyImage(self._device, image, None)
            raise

        return SharedImage(self, image, memory, int(width), int(height),
                           int(reqs.size))

    def createSemaphore(self):
        """Create a semaphore for export.

        Returns
        -------
        SharedSemaphore

        """
        export = _ExportSemaphoreCreateInfo(
            _ST_EXPORT_SEMAPHORE_CREATE_INFO, None, _HANDLE_TYPE)
        info = _SemaphoreCreateInfo(
            _ST_SEMAPHORE_CREATE_INFO,
            ctypes.cast(ctypes.pointer(export), _p), 0)
        semaphore = _nhandle()
        _check(self._vk.vkCreateSemaphore(
            self._device, ctypes.byref(info), None, ctypes.byref(semaphore)),
            'vkCreateSemaphore')
        return SharedSemaphore(self, semaphore)

    def _export(self, getHandle, infoType, obj):
        """Get a new handle for memory or a semaphore (`int`)."""
        info = _GetHandleInfo(infoType, None, obj, _HANDLE_TYPE)
        handle = _OSHandle(-1) if not _WINDOWS else _OSHandle()
        _check(getHandle(self._device, ctypes.byref(info),
                         ctypes.byref(handle)), 'Exporting a handle')
        if handle.value is None or handle.value < 0:  # NULL, or -1
            raise VulkanError("Exporting a handle gave none")
        return int(handle.value)

    def _destroyImage(self, image, memory):
        if self._device is not None:
            self._vk.vkDestroyImage(self._device, image, None)
            self._vk.vkFreeMemory(self._device, memory, None)

    def _destroySemaphore(self, semaphore):
        if self._device is not None:
            self._vk.vkDestroySemaphore(self._device, semaphore, None)

    def destroy(self):
        """Destroy the device and instance. What was exported stays valid in
        the processes that imported it."""
        if self._device is not None:
            self._vk.vkDestroyDevice(self._device, None)
            self._device = None
        if self._instance is not None:
            self._vk.vkDestroyInstance(self._instance, None)
            self._instance = None


def listDevices():
    """List the GPUs Vulkan can use, e.g. to see why none matched.

    Returns
    -------
    list of tuple
        `(name, deviceUUID, driverUUID)` for each, UUIDs as hex.

    Raises
    ------
    VulkanError
        If Vulkan isn't available.

    """
    allocator = VulkanAllocator(None, None)
    try:
        return [(name, uuids[0], uuids[1])
                for device, name, uuids in allocator._devices()]
    finally:
        allocator.destroy()
