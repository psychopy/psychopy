:mod:`psychopy.tools.gltools`
----------------------------------------

.. automodule:: psychopy.tools.gltools
.. currentmodule:: psychopy.tools.gltools

Overview
~~~~~~~~

.. autosummary::
    createProgram
    createProgramObjectARB
    compileShader
    compileShaderObjectARB
    embedShaderSourceDefs
    deleteObject
    deleteObjectARB
    attachShader
    attachObjectARB
    detachShader
    detachObjectARB
    linkProgram
    linkProgramObjectARB
    validateProgram
    validateProgramARB
    useProgram
    useProgramObjectARB
    getInfoLog
    getUniformLocations
    getAttribLocations
    createQueryObject
    beginQuery
    endQuery
    getQuery
    getAbsTimeGPU
    createFBO
    attach
    isComplete
    deleteFBO
    blitFBO
    useFBO
    createRenderbuffer
    deleteRenderbuffer
    createTexImage2D
    createTexImage2DMultisample
    deleteTexture
    VertexArrayInfo
    createVAO
    drawVAO
    deleteVAO
    VertexBufferInfo
    createVBO
    bindVBO
    unbindVBO
    mapBuffer
    unmapBuffer
    deleteVBO
    setVertexAttribPointer
    enableVertexAttribArray
    disableVertexAttribArray
    createMaterial
    useMaterial
    createLight
    useLights
    setAmbientLight
    ObjMeshInfo
    loadObjFile
    loadMtlFile
    createUVSphere
    createPlane
    createMeshGridFromArrays
    createMeshGrid
    createBox
    transformMeshPosOri
    calculateVertexNormals
    getIntegerv
    getFloatv
    getString
    getOpenGLInfo
    
Details
~~~~~~~

.. autofunction:: createProgram
.. autofunction:: createProgramObjectARB
.. autofunction:: compileShader
.. autofunction:: compileShaderObjectARB
.. autofunction:: embedShaderSourceDefs
.. autofunction:: deleteObject
.. autofunction:: deleteObjectARB
.. autofunction:: attachShader
.. autofunction:: attachObjectARB
.. autofunction:: detachShader
.. autofunction:: detachObjectARB
.. autofunction:: linkProgram
.. autofunction:: linkProgramObjectARB
.. autofunction:: validateProgram
.. autofunction:: validateProgramARB
.. autofunction:: useProgram
.. autofunction:: useProgramObjectARB
.. autofunction:: getInfoLog
.. autofunction:: getUniformLocations
.. autofunction:: getAttribLocations
.. autofunction:: createQueryObject
.. autofunction:: beginQuery
.. autofunction:: endQuery
.. autofunction:: getQuery
.. autofunction:: getAbsTimeGPU
.. autofunction:: createFBO
.. autofunction:: attach
.. autofunction:: isComplete
.. autofunction:: deleteFBO
.. autofunction:: blitFBO
.. autofunction:: useFBO
.. autofunction:: createRenderbuffer
.. autofunction:: deleteRenderbuffer
.. autofunction:: createTexImage2D
.. autofunction:: createTexImage2DMultisample
.. autofunction:: deleteTexture
.. autofunction:: createVAO
.. autofunction:: drawVAO
.. autofunction:: deleteVAO
.. autofunction:: createVBO
.. autofunction:: bindVBO
.. autofunction:: unbindVBO
.. autofunction:: mapBuffer
.. autofunction:: unmapBuffer
.. autofunction:: deleteVBO
.. autofunction:: setVertexAttribPointer
.. autofunction:: enableVertexAttribArray
.. autofunction:: disableVertexAttribArray
.. autofunction:: createMaterial
.. autofunction:: useMaterial
.. autofunction:: createLight
.. autofunction:: useLights
.. autofunction:: setAmbientLight
.. autofunction:: loadObjFile
.. autofunction:: loadMtlFile
.. autofunction:: createUVSphere
.. autofunction:: createPlane
.. autofunction:: createMeshGridFromArrays
.. autofunction:: createMeshGrid
.. autofunction:: createBox
.. autofunction:: transformMeshPosOri
.. autofunction:: calculateVertexNormals
.. autofunction:: getIntegerv
.. autofunction:: getFloatv
.. autofunction:: getString
.. autofunction:: getOpenGLInfo


Examples
~~~~~~~~
**Working with Framebuffer Objects (FBOs):**

Creating an empty framebuffer with no attachments::

    fbo = createFBO()  # invalid until attachments are added

Create a render target with multiple color texture attachments::

    colorTex = createTexImage2D(1024,1024)  # empty texture
    depthRb = createRenderbuffer(800,600,internalFormat=GL.GL_DEPTH24_STENCIL8)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo.id)
    attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
    attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
    attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
    # or attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

Attach FBO images using a context. This automatically returns to the previous
FBO binding state when complete. This is useful if you don't know the current
binding state::

    with useFBO(fbo):
        attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
        attach(GL.GL_STENCIL_ATTACHMENT, depthRb)

How to set userData some custom function might access::

    fbo.userData['flags'] = ['left_eye', 'clear_before_use']

Binding an FBO for drawing/reading::

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fb.id)

Depth-only framebuffers are valid, sometimes need for generating shadows::

    depthTex = createTexImage2D(800, 600,
                                internalFormat=GL.GL_DEPTH_COMPONENT24,
                                pixelFormat=GL.GL_DEPTH_COMPONENT)
    fbo = createFBO([(GL.GL_DEPTH_ATTACHMENT, depthTex)])

Deleting a framebuffer when done with it. This invalidates the framebuffer's ID
and makes it available for use::

    deleteFBO(fbo)

