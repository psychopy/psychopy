:mod:`psychopy.tools.gltools`
----------------------------------------

.. automodule:: psychopy.tools.gltools
.. currentmodule:: psychopy.tools.gltools
    
.. autosummary:: 

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
    createVBO
    createVAO
    drawVAO
    deleteVBO
    deleteVAO
    createMaterial
    useMaterial
    createLight
    useLights
    setAmbientLight
    loadObjFile
    loadMtlFile
    getIntegerv
    getFloatv
    getString
    getOpenGLInfo
    
Function details
~~~~~~~~~~~~~~~~~~~~~~~

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
.. autofunction:: createVBO
.. autofunction:: createVAO
.. autofunction:: drawVAO
.. autofunction:: deleteVBO
.. autofunction:: deleteVAO
.. autofunction:: createMaterial
.. autofunction:: useMaterial
.. autofunction:: createLight
.. autofunction:: useLights
.. autofunction:: setAmbientLight
.. autofunction:: loadObjFile
.. autofunction:: loadMtlFile
.. autofunction:: getIntegerv
.. autofunction:: getFloatv
.. autofunction:: getString
.. autofunction:: getOpenGLInfo

Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~
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

