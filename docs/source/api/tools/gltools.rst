:mod:`psychopy.tools.gltools`
-----------------------------

.. automodule:: psychopy.tools.gltools
.. currentmodule:: psychopy.tools.gltools

Shaders
~~~~~~~

Tools for creating, compiling, using, and inspecting shader programs.

.. autosummary::
    :toctree: ../generated/

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

Query
~~~~~

Tools for using OpenGL query objects.

.. autosummary::
    :toctree: ../generated/

    createQueryObject
    QueryObjectInfo
    beginQuery
    endQuery
    getQuery
    getAbsTimeGPU

Framebuffer Objects (FBO)
~~~~~~~~~~~~~~~~~~~~~~~~~

Tools for creating Framebuffer Objects (FBOs).

.. autosummary::
    :toctree: ../generated/

    createFBO
    attach
    isComplete
    deleteFBO
    blitFBO
    useFBO

Renderbuffers
~~~~~~~~~~~~~

Tools for creating Renderbuffers.

.. autosummary::
    :toctree: ../generated/

    createRenderbuffer
    deleteRenderbuffer


Textures
~~~~~~~~

Tools for creating textures.

.. autosummary::
    :toctree: ../generated/

    createTexImage2D
    createTexImage2dFromFile
    createTexImage2DMultisample
    deleteTexture
    bindTexture
    unbindTexture
    createCubeMap

Vertex Buffer/Array Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tools for creating and working with Vertex Buffer Objects (VBOs) and Vertex
Array Objects (VAOs).

.. autosummary::
    :toctree: ../generated/

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

Materials and Lighting
~~~~~~~~~~~~~~~~~~~~~~

Tools for specifying the appearance of faces and shading. Note that these tools
use the legacy OpenGL pipeline which may not be available on your platform. Use
fragment/vertex shaders instead for newer applications.

.. autosummary::
    :toctree: ../generated/

    createMaterial
    useMaterial
    createLight
    useLights
    setAmbientLight

Meshes
~~~~~~

Tools for loading or procedurally generating meshes (3D models).

.. autosummary::
    :toctree: ../generated/

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

Miscellaneous
~~~~~~~~~~~~~

Miscellaneous tools for working with OpenGL.

.. autosummary::
    :toctree: ../generated/

    getIntegerv
    getFloatv
    getString
    getOpenGLInfo
    getModelViewMatrix
    getProjectionMatrix


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
