"""Tests for 3D stimulus classes in `psychopy.visual.stim3d`.
"""
import ctypes

import numpy as np
import pytest
from PIL import Image

from psychopy import visual
from psychopy.colors import Color
import psychopy.tools.gltools as gt
import psychopy.tools.mathtools as mt
import psychopy.tools.pygletgl as GL
import psychopy.tools.viewtools as vt
from psychopy.visual.stim3d import (
    LightSource, SceneSkybox, BlinnPhongMaterial, SphereStim, BoxStim,
    PlaneStim, ObjMeshStim)


def _writeObjFile(folder):
    """Write a unit cube as an OBJ file with an associated MTL file. The +X and
    -X faces use material `red`, the rest use `blue`.

    Returns
    -------
    pathlib.Path
        Path to the OBJ file.

    """
    vertices, texCoords, normals, faces = gt.createBox(1.0)

    lines = ['mtllib cube.mtl']
    lines += ['v {} {} {}'.format(*v) for v in vertices]
    lines += ['vt {} {}'.format(*t) for t in texCoords]
    lines += ['vn {} {} {}'.format(*n) for n in normals]

    # each box face is two triangles, the first two faces are +X and -X
    groups = {'red': faces[:4], 'blue': faces[4:]}
    for name, tris in groups.items():
        lines.append('usemtl ' + name)
        for tri in tris:
            # OBJ indices are 1-based, the same index is used for v/vt/vn
            lines.append(
                'f ' + ' '.join('{0}/{0}/{0}'.format(i + 1) for i in tri))

    objFile = folder / 'cube.obj'
    objFile.write_text('\n'.join(lines) + '\n')
    (folder / 'cube.mtl').write_text(
        'newmtl red\nNs 10\nKa 0 0 0\nKd 1 0 0\nKs 0 0 0\n\n'
        'newmtl blue\nNs 20\nKa 0 0 0\nKd 0 0 1\nKs 0 0 0\n')

    return objFile


class TestStim3D:

    @classmethod
    def setup_class(cls):
        cls.win = visual.Window(
            [128, 128], pos=[50, 50], allowGUI=False, autoLog=False)
        cls.win.scrWidthPIX = 128  # needed by `setPerspectiveView`

        # white light at the viewer so faces pointing at it are lit
        cls.light = LightSource(
            cls.win, pos=(0., 0., 0.), diffuseColor=(1, 1, 1),
            specularColor=(-1, -1, -1), lightType='point')
        cls.win.lights = [cls.light]

    @classmethod
    def teardown_class(cls):
        cls.win.close()

    def setup_method(self):
        self.win.flip()

    def _render(self, *stims):
        """Draw stimuli with a perspective view and return the back buffer as
        an RGB array.
        """
        self.win.setPerspectiveView()
        self.win.useLights = True
        for stim in stims:
            stim.draw()
        self.win.useLights = False
        self.win.resetEyeTransform()

        frame = np.asarray(
            self.win.getMovieFrame(buffer='back'), dtype=int)[:, :, :3]
        self.win.movieFrames = []
        self.win.flip()

        return frame

    @staticmethod
    def _centerPixel(frame):
        return frame[frame.shape[0] // 2, frame.shape[1] // 2]

    def _assertDrawn(self, frame):
        """Check the center of the frame differs from the background."""
        background = frame[0, 0]
        assert np.abs(self._centerPixel(frame) - background).sum() > 30

    # --------------------------------------------------------------------------
    # LightSource
    #

    def test_light_type(self):
        light = LightSource(self.win, pos=(1, 2, 3), lightType='point')
        assert light.pos == pytest.approx([1, 2, 3])
        assert light._pos[3] == 1.0  # point lights have w=1

        light.lightType = 'directional'
        assert light._pos[3] == 0.0  # directional lights have w=0

        with pytest.raises(ValueError):
            light.lightType = 'spot'

    def test_light_colors(self):
        light = LightSource(
            self.win, diffuseColor=(1, -1, -1), specularColor=(-1, 1, -1),
            ambientColor=(-1, -1, 1), colorSpace='rgb')
        assert light.diffuseRGB == pytest.approx([1, 0, 0, 1])
        assert light.specularRGB == pytest.approx([0, 1, 0, 1])
        assert light.ambientRGB == pytest.approx([0, 0, 1, 1])

        light.attenuation = (1, 0.5, 0.25)
        assert light.attenuation.dtype == np.float32
        assert light.attenuation == pytest.approx([1, 0.5, 0.25])

    # --------------------------------------------------------------------------
    # BlinnPhongMaterial
    #

    def test_material_colors(self):
        mat = BlinnPhongMaterial(
            self.win, diffuseColor=(1, -1, -1), specularColor=(-1, 1, -1),
            ambientColor=(-1, -1, 1), emissionColor=(1, 1, 1))
        assert mat.diffuseRGB == pytest.approx([1, 0, 0])
        assert mat.specularRGB == pytest.approx([0, 1, 0])
        assert mat.ambientRGB == pytest.approx([0, 0, 1])
        assert mat.emissionRGB == pytest.approx([1, 1, 1])

    def test_material_pointers_track_colors(self):
        # pointers passed to OpenGL are created once, they must reflect colors
        # set afterwards
        mat = BlinnPhongMaterial(self.win)
        mat.diffuseColor = (1, -1, -1)
        mat.specularColor = (-1, 1, -1)
        mat.ambientColor = (-1, -1, 1)
        mat.emissionColor = (1, 1, -1)
        assert list(mat._ptrDiffuse) == pytest.approx([1, 0, 0, 1])
        assert list(mat._ptrSpecular) == pytest.approx([0, 1, 0, 1])
        assert list(mat._ptrAmbient) == pytest.approx([0, 0, 1, 1])
        assert list(mat._ptrEmission) == pytest.approx([1, 1, 0, 1])

    def test_material_face_and_shininess(self):
        mat = BlinnPhongMaterial(self.win, shininess=5)
        assert isinstance(mat.shininess, float)

        for face, glFace in [('front', GL.GL_FRONT), ('back', GL.GL_BACK),
                             ('both', GL.GL_FRONT_AND_BACK)]:
            mat.face = face
            assert mat.face == glFace

        with pytest.raises(ValueError):
            mat.face = 'side'

    def test_material_end_restores_defaults(self):
        mat = BlinnPhongMaterial(
            self.win, specularColor=(1, 1, 1), emissionColor=(1, 1, 1),
            shininess=50)
        mat.begin()
        mat.end(clear=True)

        # `end` enables `GL_COLOR_MATERIAL` so diffuse and ambient track
        # `glColor`, only check components which aren't affected by that
        specular = (GL.GLfloat * 4)()
        emission = (GL.GLfloat * 4)()
        shininess = (GL.GLfloat * 1)()
        GL.glGetMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, specular)
        GL.glGetMaterialfv(GL.GL_FRONT, GL.GL_EMISSION, emission)
        GL.glGetMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, shininess)
        assert list(specular) == pytest.approx([0.0, 0.0, 0.0, 1.0])
        assert list(emission) == pytest.approx([0.0, 0.0, 0.0, 1.0])
        assert shininess[0] == pytest.approx(0.0)

    # --------------------------------------------------------------------------
    # Rigid body stimuli
    #

    @pytest.mark.parametrize('stimClass, kwargs', [
        (SphereStim, {'radius': 0.5}),
        (BoxStim, {'size': (0.6, 0.6, 0.6)}),
        (PlaneStim, {'size': (1.0, 1.0)}),
    ])
    def test_draw_without_material(self, stimClass, kwargs):
        stim = stimClass(
            self.win, pos=(0, 0, -3), color=(1, -1, -1), **kwargs)
        frame = self._render(stim)
        self._assertDrawn(frame)

        # the stimulus color should dominate
        r, g, b = self._centerPixel(frame)
        assert r > g and r > b

    def test_draw_with_material(self):
        stim = BoxStim(self.win, size=(0.6, 0.6, 0.6), pos=(0, 0, -3))
        stim.material = BlinnPhongMaterial(
            self.win, diffuseColor=(-1, -1, 1), specularColor=(-1, -1, -1))
        frame = self._render(stim)
        self._assertDrawn(frame)

        r, g, b = self._centerPixel(frame)
        assert b > r and b > g

    def test_draw_with_texture(self):
        texData = np.zeros((4, 4, 4), dtype=np.uint8)
        texData[:, :, 1] = 255  # green
        texData[:, :, 3] = 255
        texture = gt.createTexImage2D(
            4, 4, internalFormat=GL.GL_RGBA, pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE, data=texData.ctypes,
            unpackAlignment=1)

        stim = PlaneStim(self.win, size=(1.0, 1.0), pos=(0, 0, -3))
        stim.material = BlinnPhongMaterial(
            self.win, diffuseColor=(1, 1, 1), specularColor=(-1, -1, -1),
            diffuseTexture=texture)
        frame = self._render(stim)
        self._assertDrawn(frame)

        r, g, b = self._centerPixel(frame)
        assert g > r and g > b

    def test_draw_restores_draw3d(self):
        stim = SphereStim(self.win, pos=(0, 0, -3))

        # 3D state is disabled after drawing if it was disabled before
        self.win.draw3d = False
        stim.draw()
        assert self.win.draw3d is False
        assert self.win.depthTest is False

        # 3D state is left on if the caller enabled it
        self.win.draw3d = True
        stim.draw()
        assert self.win.draw3d is True
        assert self.win.depthTest is True
        self.win.draw3d = False

    def test_draw_does_not_leak_matrix(self):
        stim = SphereStim(self.win, pos=(1, 2, -3))
        before = (GL.GLfloat * 16)()
        after = (GL.GLfloat * 16)()
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, before)
        stim.draw()
        GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, after)
        assert list(after) == pytest.approx(list(before))

    def test_pose(self):
        stim = BoxStim(self.win, pos=(1, 2, 3))
        assert stim.pos == pytest.approx([1, 2, 3])

        stim.setPos((4, 5, 6))
        assert stim.getPos() == pytest.approx([4, 5, 6])

        stim.setOriAxisAngle((0, 1, 0), 90)
        axis, angle = stim.getOriAxisAngle()
        assert axis == pytest.approx([0, 1, 0], abs=1e-6)
        assert angle == pytest.approx(90)

        with pytest.raises(AttributeError):
            stim.thePose = object()

    def test_is_visible(self):
        stim = SphereStim(self.win, radius=0.5)
        cases = [
            ((0, 0, -3), True),     # in front of the viewer
            ((0, 0, 3), False),     # behind the viewer
            ((10, 0, -3), False),   # off to the right
            ((-10, 0, -3), False),  # off to the left
            ((0, 10, -3), False),   # above
            ((0, -10, -3), False),  # below
            ((0, 0, -1000), False), # beyond the far clipping plane
            ((0.9, 0, -3), True),   # partially on screen
        ]
        self.win.setPerspectiveView()
        try:
            for pos, expected in cases:
                stim.thePose.pos = pos
                assert stim.isVisible() is expected, pos
        finally:
            self.win.resetEyeTransform()

    def test_is_visible_without_bounds(self):
        stim = SphereStim(self.win, pos=(0, 0, 3))
        stim.thePose.bounds = None
        assert stim.isVisible() is True

    def test_ray_intersect(self):
        stim = SphereStim(self.win, radius=0.5, pos=(0, 0, -3))
        hit = stim.getRayIntersectSphere((0, 0, 0), (0, 0, -1))
        assert hit is not None
        point, dist = hit
        assert point == pytest.approx([0, 0, -2.5], abs=1e-5)
        assert dist == pytest.approx(2.5, abs=1e-5)

        assert stim.getRayIntersectSphere((0, 0, 0), (0, 1, 0)) is None

        box = BoxStim(self.win, size=(1, 1, 1), pos=(0, 0, -3))
        hit = box.getRayIntersectBounds((0, 0, 0), (0, 0, -1))
        assert hit is not None
        assert hit[1] == pytest.approx(2.5, abs=1e-5)

    # --------------------------------------------------------------------------
    # ObjMeshStim
    #

    def test_obj_load_materials(self, tmp_path):
        stim = ObjMeshStim(self.win, str(_writeObjFile(tmp_path)))
        assert set(stim.material) == {'red', 'blue'}
        assert set(stim._vao) == {'red', 'blue'}

        # MTL colors are 0-1, materials use -1 to 1
        assert stim.material['red'].diffuseRGB == pytest.approx([1, 0, 0])
        assert stim.material['blue'].diffuseRGB == pytest.approx([0, 0, 1])
        assert stim.material['blue'].shininess == 20.0

    def test_obj_draw_materials(self, tmp_path):
        stim = ObjMeshStim(
            self.win, str(_writeObjFile(tmp_path)), pos=(0, 0, -3))

        # facing the viewer is the +Z face, which uses the blue material
        frame = self._render(stim)
        self._assertDrawn(frame)
        r, g, b = self._centerPixel(frame)
        assert b > r and b > g

        # turn the +X face towards the viewer, which uses the red material
        stim.setOriAxisAngle((0, 1, 0), -90)
        frame = self._render(stim)
        self._assertDrawn(frame)
        r, g, b = self._centerPixel(frame)
        assert r > g and r > b

    def test_obj_draw_single_material(self, tmp_path):
        stim = ObjMeshStim(
            self.win, str(_writeObjFile(tmp_path)), pos=(0, 0, -3),
            loadMtllib=False)
        stim.material = BlinnPhongMaterial(
            self.win, diffuseColor=(-1, 1, -1), specularColor=(-1, -1, -1))
        frame = self._render(stim)
        self._assertDrawn(frame)
        r, g, b = self._centerPixel(frame)
        assert g > r and g > b

    def test_obj_draw_without_material(self, tmp_path):
        stim = ObjMeshStim(
            self.win, str(_writeObjFile(tmp_path)), pos=(0, 0, -3),
            loadMtllib=False, color=(1, -1, -1))
        frame = self._render(stim)
        self._assertDrawn(frame)
        r, g, b = self._centerPixel(frame)
        assert r > g and r > b

    @pytest.mark.parametrize('material', ['mtllib', 'single', None])
    def test_draw_unbinds_vao(self, tmp_path, material):
        # VAOs drawn one after another are only unbound after the last one,
        # nothing may be left bound once drawing has finished
        stim = ObjMeshStim(
            self.win, str(_writeObjFile(tmp_path)), pos=(0, 0, -3),
            loadMtllib=material == 'mtllib')
        if material == 'single':
            stim.material = BlinnPhongMaterial(self.win)
        assert len(stim._vao) > 1

        box = BoxStim(self.win, pos=(0, 0, -3))
        for thisStim in (stim, box):
            self._render(thisStim)
            binding = GL.GLint()
            GL.glGetIntegerv(GL.GL_VERTEX_ARRAY_BINDING, ctypes.byref(binding))
            assert binding.value == 0, thisStim

    # --------------------------------------------------------------------------
    # SceneSkybox
    #

    def test_skybox_without_cubemap_is_noop(self):
        sky = SceneSkybox(self.win)
        assert sky.skyCubeMap is None
        frame = self._render(sky)
        assert np.all(frame == frame[0, 0])

    def test_skybox_draw(self, tmp_path):
        faces = []
        for i in range(6):
            path = tmp_path / 'face{}.png'.format(i)
            Image.new('RGB', (8, 8), (255, 0, 0)).save(path)
            faces.append(str(path))

        sky = SceneSkybox(self.win, tex=faces)
        frame = self._render(sky)

        # the sky surrounds the viewer, so it should fill the whole frame
        assert np.all(frame[:, :, 0] > frame[:, :, 1])
        assert np.all(frame[:, :, 0] > frame[:, :, 2])
        assert self.win.draw3d is False

    def test_skybox_wrong_face_count(self, tmp_path):
        path = tmp_path / 'face.png'
        Image.new('RGB', (8, 8), (255, 0, 0)).save(path)
        with pytest.raises(ValueError):
            SceneSkybox(self.win, tex=[str(path)] * 5)

        with pytest.raises(TypeError):
            SceneSkybox(self.win, tex='face.png')


class _Stim3DRenderTest:
    """Base class for tests which render 3D stimuli and check the resulting
    pixel values.
    """

    # 8-bit framebuffer rounding
    TOL = 3

    @classmethod
    def setup_class(cls):
        cls.win = visual.Window(
            [128, 128], pos=[50, 50], allowGUI=False, autoLog=False)
        # needed by `setPerspectiveView`, which sizes the frustum using the
        # ratio of `win.size` (framebuffer pixels) to this, so match it to keep
        # the view the same regardless of the display's pixel scale (Retina)
        cls.win.scrWidthPIX = cls.win.size[0]

    @classmethod
    def teardown_class(cls):
        cls.win.close()

    def setup_method(self):
        self.win.flip()

    def _light(self, pos, lightType='directional', diffuse=(1, 1, 1),
               specular=(-1, -1, -1), ambient=(-1, -1, -1),
               attenuation=(1, 0, 0)):
        """Make a light source, colors are signed RGB."""
        return LightSource(
            self.win, pos=pos, lightType=lightType, diffuseColor=diffuse,
            specularColor=specular, ambientColor=ambient,
            attenuation=attenuation, colorSpace='rgb')

    def _material(self, diffuse=(-1, -1, -1), specular=(-1, -1, -1),
                  ambient=(-1, -1, -1), emission=(-1, -1, -1), shininess=10.):
        """Make a material, colors are signed RGB and black by default."""
        return BlinnPhongMaterial(
            self.win, diffuseColor=diffuse, specularColor=specular,
            ambientColor=ambient, emissionColor=emission, shininess=shininess)

    def _plane(self, material=None, size=(4, 4), **kwargs):
        """Plane facing the viewer which fills the frame."""
        stim = PlaneStim(self.win, size=size, pos=(0, 0, -3), **kwargs)
        stim.material = material
        return stim

    def _render(self, stim, lights=(), sceneAmbient=(0, 0, 0),
                useLights=True):
        """Draw `stim` lit by `lights` and return the back buffer as an RGB
        array.

        Lights are assigned after the view is set, so their positions are in
        scene coordinates.
        """
        self.win.setPerspectiveView()
        self.win.lights = list(lights)
        self.win.ambientLight = sceneAmbient
        self.win.useLights = useLights
        stim.draw()
        self.win.useLights = False
        self.win.lights = []
        self.win.ambientLight = (0, 0, 0)
        self.win.resetEyeTransform()

        frame = np.asarray(
            self.win.getMovieFrame(buffer='back'), dtype=int)[:, :, :3]
        self.win.movieFrames = []
        self.win.flip()

        return frame

    @staticmethod
    def _pixel(frame, x=0., y=0.):
        """Get a pixel at normalized window coordinates, (0, 0) is the center
        and (1, 1) the top-right corner.
        """
        h, w = frame.shape[:2]
        col = int(round((x + 1.) / 2. * (w - 1)))
        row = int(round((1. - y) / 2. * (h - 1)))
        return frame[row, col]

    def _assertColor(self, actual, expected):
        assert np.all(np.abs(np.asarray(actual) - expected) <= self.TOL), \
            "got {}, expected {}".format(list(actual), list(expected))

    def _project(self, point):
        """Get the normalized window coordinates of a point in the scene, for
        use with `_pixel`.
        """
        self.win.setPerspectiveView()
        mvp = np.matmul(self.win.projectionMatrix, self.win.viewMatrix)
        self.win.resetEyeTransform()

        clip = np.matmul(mvp, np.append(np.asarray(point, float), 1.))
        return clip[:2] / clip[3]


class TestStim3DLighting(_Stim3DRenderTest):
    """Tests for lighting and shading of 3D stimuli.

    Expected pixel values are computed from the Blinn-Phong lighting model the
    shaders implement. Unless a test says otherwise, lights have black ambient
    and specular colors and the scene ambient light is black, so only the
    diffuse component contributes.
    """

    # direction of a light behind surfaces facing the viewer. Not directly
    # behind, since the specular halfway vector is undefined when the light
    # and view directions are exactly opposite.
    BEHIND = (0, 1, -1)

    # --------------------------------------------------------------------------
    # Diffuse
    #

    def test_unlit_is_black(self):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        self._assertColor(self._pixel(self._render(plane)), (0, 0, 0))

    def test_use_lights_disabled(self):
        # lights have no effect on materials unless `useLights` is set
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        frame = self._render(
            plane, [self._light((0, 0, 1))], useLights=False)
        self._assertColor(self._pixel(frame), (0, 0, 0))

    @pytest.mark.parametrize('angle', [0, 45, 60, 75])
    def test_lambert_cosine(self, angle):
        # diffuse intensity is proportional to the cosine of the angle between
        # the surface normal and the light direction
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        plane.setOriAxisAngle((0, 1, 0), angle)
        frame = self._render(plane, [self._light((0, 0, 1))])

        expected = 255 * np.cos(np.radians(angle))
        self._assertColor(self._pixel(frame), (expected,) * 3)

    def test_light_behind_surface(self):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        frame = self._render(plane, [self._light(self.BEHIND)])
        self._assertColor(self._pixel(frame), (0, 0, 0))

    @pytest.mark.parametrize('lightPos, litSide, darkSide', [
        ((1, 0, 0), (0.3, 0), (-0.3, 0)),   # from the right
        ((-1, 0, 0), (-0.3, 0), (0.3, 0)),  # from the left
        ((0, 1, 0), (0, 0.3), (0, -0.3)),   # from above
        ((0, -1, 0), (0, -0.3), (0, 0.3)),  # from below
    ])
    def test_directional_light_shading(self, lightPos, litSide, darkSide):
        sphere = SphereStim(self.win, radius=1.0, pos=(0, 0, -3))
        sphere.material = self._material(diffuse=(1, 1, 1))
        frame = self._render(sphere, [self._light(lightPos)])

        lit = self._pixel(frame, *litSide)
        dark = self._pixel(frame, *darkSide)
        assert lit.sum() > 3 * 50, lit
        self._assertColor(dark, (0, 0, 0))  # facing away from the light

    def test_directional_light_is_uniform(self):
        # a directional light hits every point of a plane at the same angle
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        plane.setOriAxisAngle((0, 1, 0), 45)
        frame = self._render(plane, [self._light((0, 0, 1))])
        self._assertColor(
            self._pixel(frame, -0.2, 0), self._pixel(frame, 0.2, 0))

    def test_point_light_position(self):
        # a point light near one side of a plane lights that side more
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        frame = self._render(
            plane, [self._light((0.75, 0, -2.5), lightType='point')])
        right = self._pixel(frame, 0.4, 0)
        left = self._pixel(frame, -0.4, 0)
        assert right.sum() > left.sum() + 3 * 20, (left, right)

    @pytest.mark.parametrize('attenuation', [
        (1, 0, 0),       # none
        (2, 0, 0),       # constant
        (1, 1 / 3., 0),  # linear
        (1, 0, 1 / 9.),  # quadratic
        (1, 0, 1 / 3.),
    ])
    def test_point_light_attenuation(self, attenuation):
        # light at the viewer, the center of the plane is 3 units away
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        light = self._light(
            (0, 0, 0), lightType='point', attenuation=attenuation)
        frame = self._render(plane, [light])

        k0, k1, k2 = attenuation
        expected = 255 / (k0 + k1 * 3 + k2 * 9)
        self._assertColor(self._pixel(frame), (expected,) * 3)

    def test_directional_light_not_attenuated(self):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        light = self._light((0, 0, 1), attenuation=(1, 1, 1))
        self._assertColor(
            self._pixel(self._render(plane, [light])), (255, 255, 255))

    @pytest.mark.parametrize('lightColor, expected', [
        ((1, -1, -1), (255, 0, 0)),
        ((-1, 1, -1), (0, 255, 0)),
        ((-1, -1, 1), (0, 0, 255)),
        ((0, 0, 0), (128, 128, 128)),  # signed RGB zero is mid-grey
    ])
    def test_light_color(self, lightColor, expected):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        frame = self._render(plane, [self._light((0, 0, 1), diffuse=lightColor)])
        self._assertColor(self._pixel(frame), expected)

    @pytest.mark.parametrize('lightColor, materialColor, expected', [
        ((1, 1, 1), (1, -1, 1), (255, 0, 255)),
        ((1, 1, 1), (0, 0, 0), (128, 128, 128)),
        ((1, -1, -1), (-1, 1, -1), (0, 0, 0)),  # red light on green surface
        ((1, 1, -1), (1, -1, 1), (255, 0, 0)),  # yellow light on magenta
    ])
    def test_material_modulates_light(self, lightColor, materialColor,
                                      expected):
        plane = self._plane(self._material(diffuse=materialColor))
        frame = self._render(
            plane, [self._light((0, 0, 1), diffuse=lightColor)])
        self._assertColor(self._pixel(frame), expected)

    def test_multiple_lights_add(self):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        halfGrey = (0, 0, 0)
        frame = self._render(plane, [self._light((0, 0, 1), diffuse=halfGrey)])
        self._assertColor(self._pixel(frame), (128, 128, 128))

        frame = self._render(plane, [self._light((0, 0, 1), diffuse=halfGrey),
                                     self._light((0, 0, 1), diffuse=halfGrey)])
        self._assertColor(self._pixel(frame), (255, 255, 255))

        frame = self._render(
            plane, [self._light((0, 0, 1), diffuse=(1, -1, -1)),
                    self._light((0, 0, 1), diffuse=(-1, -1, 1))])
        self._assertColor(self._pixel(frame), (255, 0, 255))

    def test_max_lights(self):
        # shaders are built for up to 8 lights, each adds 1/8 intensity here
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        eighth = 2 / 8. - 1  # signed RGB
        lights = [self._light((0, 0, 1), diffuse=(eighth,) * 3)
                  for _ in range(8)]
        frame = self._render(plane, lights)
        self._assertColor(self._pixel(frame), (255, 255, 255))

    def test_textured_material_is_lit(self):
        texData = np.zeros((4, 4, 4), dtype=np.uint8)
        texData[:, :, 1] = 255  # green
        texData[:, :, 3] = 255
        texture = gt.createTexImage2D(
            4, 4, internalFormat=GL.GL_RGBA, pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE, data=texData.ctypes,
            unpackAlignment=1)
        material = self._material(diffuse=(1, 1, 1))
        material.diffuseTexture = texture
        plane = self._plane(material)

        # texture colors are modulated by lighting, not drawn as-is
        plane.setOriAxisAngle((0, 1, 0), 60)
        frame = self._render(plane, [self._light((0, 0, 1))])
        self._assertColor(self._pixel(frame), (0, 128, 0))

        frame = self._render(plane, [self._light(self.BEHIND)])
        self._assertColor(self._pixel(frame), (0, 0, 0))

    # --------------------------------------------------------------------------
    # Ambient
    #

    def test_scene_ambient(self):
        # light from behind, so only ambient contributes. Scene ambient is
        # modulated by the material diffuse color.
        plane = self._plane(self._material(diffuse=(1, -1, 1)))
        frame = self._render(
            plane, [self._light(self.BEHIND)], sceneAmbient=(.5, .5, .5))
        self._assertColor(self._pixel(frame), (128, 0, 128))

    def test_light_ambient(self):
        # light ambient is modulated by the material ambient and diffuse colors
        plane = self._plane(
            self._material(diffuse=(1, 1, 1), ambient=(1, 1, 1)))
        light = self._light(self.BEHIND, ambient=(0, 0, 0))  # 50% grey
        frame = self._render(plane, [light])
        self._assertColor(self._pixel(frame), (128, 128, 128))

        # no material ambient, no light ambient contribution
        plane.material = self._material(diffuse=(1, 1, 1))
        frame = self._render(plane, [light])
        self._assertColor(self._pixel(frame), (0, 0, 0))

    def test_light_default_ambient(self):
        # lights add no ambient light by default, like `BlinnPhongMaterial`
        light = LightSource(self.win, pos=self.BEHIND, lightType='directional')
        assert light.diffuseRGB == pytest.approx([1, 1, 1, 1])
        assert light.specularRGB == pytest.approx([1, 1, 1, 1])
        assert light.ambientRGB == pytest.approx([0, 0, 0, 1])

        # stimuli without a material use their color as the ambient color
        plane = self._plane(color=(1, 1, 1))
        frame = self._render(plane, [light])
        self._assertColor(self._pixel(frame), (0, 0, 0))

    def test_scene_ambient_without_lights(self):
        # the diffuse color multiplied by the scene ambient color, the same as
        # the scene ambient contribution when there are lights
        plane = self._plane(self._material(diffuse=(1, -1, 1)))
        before = self._pixel(self._render(plane, sceneAmbient=(.5, .5, .5)))
        self._assertColor(before, (128, 0, 128))

        withLight = self._pixel(self._render(
            plane, [self._light(self.BEHIND, ambient=(1, 1, 1))],
            sceneAmbient=(.5, .5, .5)))
        self._assertColor(withLight, before)

        # previously assigned lights don't affect the result
        after = self._pixel(self._render(plane, sceneAmbient=(.5, .5, .5)))
        self._assertColor(after, before)

    # --------------------------------------------------------------------------
    # Emission
    #

    def test_emission_without_lights(self):
        plane = self._plane(self._material(emission=(-1, 0, -1)))
        self._assertColor(self._pixel(self._render(plane)), (0, 128, 0))

    def test_emission_adds_to_diffuse(self):
        plane = self._plane(
            self._material(diffuse=(-1, 0, -1), emission=(0, -1, -1)))
        frame = self._render(plane, [self._light((0, 0, 1))])
        self._assertColor(self._pixel(frame), (128, 128, 0))

    @pytest.mark.parametrize('nLights', [0, 1, 2, 8])
    def test_emission_independent_of_light_count(self, nLights):
        plane = self._plane(self._material(emission=(-0.5, -0.5, -0.5)))
        lights = [self._light(self.BEHIND) for _ in range(nLights)]
        frame = self._render(plane, lights)
        self._assertColor(self._pixel(frame), (64, 64, 64))

    @pytest.mark.parametrize('nLights', [1, 2, 8])
    def test_scene_ambient_independent_of_light_count(self, nLights):
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        lights = [self._light(self.BEHIND) for _ in range(nLights)]
        frame = self._render(plane, lights, sceneAmbient=(.25, .25, .25))
        self._assertColor(self._pixel(frame), (64, 64, 64))

    # --------------------------------------------------------------------------
    # Specular
    #

    def _specularFrame(self, shininess, materialSpecular=(1, 1, 1)):
        """Plane with only a specular component, lit by a point light at the
        viewer so the highlight is at the center.
        """
        plane = self._plane(
            self._material(specular=materialSpecular, shininess=shininess))
        light = self._light(
            (0, 0, 0), lightType='point', diffuse=(-1, -1, -1),
            specular=(1, 1, 1))
        return self._render(plane, [light])

    def test_specular_highlight(self):
        frame = self._specularFrame(shininess=10)
        # the highlight is brightest where the surface reflects the light
        # towards the viewer
        self._assertColor(self._pixel(frame), (255, 255, 255))
        assert self._pixel(frame, 0.5, 0).sum() < 3 * 200

    def test_no_specular_highlight(self):
        frame = self._specularFrame(shininess=10, materialSpecular=(-1, -1, -1))
        self._assertColor(self._pixel(frame), (0, 0, 0))

    def test_shininess_narrows_highlight(self):
        def highlightArea(frame):
            return np.count_nonzero(frame.sum(axis=2) > 3 * 128)

        dull = highlightArea(self._specularFrame(shininess=2))
        shiny = highlightArea(self._specularFrame(shininess=64))
        assert 0 < shiny < dull

    def test_specular_color(self):
        plane = self._plane(self._material(specular=(-1, 1, -1)))
        light = self._light(
            (0, 0, 0), lightType='point', diffuse=(-1, -1, -1),
            specular=(1, 1, 1))
        self._assertColor(
            self._pixel(self._render(plane, [light])), (0, 255, 0))

    # --------------------------------------------------------------------------
    # Opacity
    #

    def _background(self):
        """Color of the background, measured at the corner of a frame with a
        tiny plane at its center.
        """
        plane = self._plane(self._material(diffuse=(1, 1, 1)), size=(.1, .1))
        return self._render(plane, [self._light((0, 0, 1))])[0, 0]

    def _blend(self, color, opacity):
        """Expected color of `color` drawn over the background."""
        return (opacity * np.asarray(color) +
                (1 - opacity) * self._background())

    def test_material_opacity_value(self):
        mat = BlinnPhongMaterial(self.win, diffuseColor=(1, 1, 1), opacity=0.5)
        assert mat.opacity == 0.5
        assert mat._diffuseRGB[3] == pytest.approx(0.5)

        # combined with the alpha of the diffuse color, and kept when the
        # diffuse color changes
        mat.diffuseColor = Color((1, 1, 1, 0.5), 'rgba')
        assert mat._diffuseRGB[3] == pytest.approx(0.25)
        assert list(mat._ptrDiffuse)[3] == pytest.approx(0.25)

        mat.opacity = 1.0
        assert mat._diffuseRGB[3] == pytest.approx(0.5)

    def test_transparent_is_background(self):
        # nothing should be drawn when fully transparent, even when lit
        plane = self._plane(
            self._material(diffuse=(1, 1, 1), emission=(1, 1, 1)))
        plane.material.opacity = 0.0
        frame = self._render(plane, [self._light((0, 0, 1))])
        background = self._background()
        assert np.abs(background - 255).sum() > 30  # differs from the plane
        assert np.all(frame == background)

    @pytest.mark.parametrize('nLights', [0, 1, 2, 8])
    @pytest.mark.parametrize('opacity', [0.25, 0.5, 0.75, 1.0])
    def test_material_opacity(self, opacity, nLights):
        # opacity doesn't depend on how many lights there are, white lights
        # make the plane white, without lights it's black
        plane = self._plane(self._material(diffuse=(1, 1, 1)))
        plane.material.opacity = opacity
        lights = [self._light((0, 0, 1)) for _ in range(nLights)]
        frame = self._render(plane, lights)

        color = (255, 255, 255) if nLights else (0, 0, 0)
        self._assertColor(self._pixel(frame), self._blend(color, opacity))

    def test_emission_opacity(self):
        plane = self._plane(self._material(emission=(1, -1, -1)))
        plane.material.opacity = 0.5
        frame = self._render(plane)
        self._assertColor(self._pixel(frame), self._blend((255, 0, 0), 0.5))

    @pytest.mark.parametrize('texAlpha', [0, 128, 255])
    def test_texture_opacity(self, texAlpha):
        texData = np.zeros((4, 4, 4), dtype=np.uint8)
        texData[:, :, 1] = 255  # green
        texData[:, :, 3] = texAlpha
        texture = gt.createTexImage2D(
            4, 4, internalFormat=GL.GL_RGBA, pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE, data=texData.ctypes,
            unpackAlignment=1)
        material = self._material(diffuse=(1, 1, 1))
        material.diffuseTexture = texture
        material.opacity = 0.5
        plane = self._plane(material)
        frame = self._render(plane, [self._light((0, 0, 1))])

        # texture alpha is multiplied with the material opacity
        opacity = 0.5 * texAlpha / 255.
        self._assertColor(
            self._pixel(frame), self._blend((0, 255, 0), opacity))

    @pytest.mark.parametrize('stimClass, kwargs', [
        (PlaneStim, {'size': (4, 4)}),
        (SphereStim, {'radius': 1.0}),
    ])
    def test_opacity_without_material(self, stimClass, kwargs):
        stim = stimClass(
            self.win, pos=(0, 0, -3), color=(1, 1, 1), opacity=0.5, **kwargs)
        frame = self._render(stim, [self._light((0, 0, 1))])
        self._assertColor(
            self._pixel(frame), self._blend((255, 255, 255), 0.5))

    # --------------------------------------------------------------------------
    # Stimuli without a material
    #

    # colors are signed RGB, these used to be passed to OpenGL as-is so
    # negative channels were clamped to zero, or with ambient light multiplied
    # together to give positive ones (e.g. red turned white)
    @pytest.mark.parametrize('color, lightPos, lightAmbient, expected', [
        pytest.param((1, -1, -1), (0, 0, 1), (-1, -1, -1), (255, 0, 0),
                     id='red'),
        pytest.param((-1, -1, -1), (0, 0, 1), (-1, -1, -1), (0, 0, 0),
                     id='black'),
        pytest.param((0, 0, 0), (0, 0, 1), (-1, -1, -1), (128, 128, 128),
                     id='grey'),
        pytest.param((1, -1, -1), BEHIND, (1, 1, 1), (255, 0, 0),
                     id='red-ambient'),
    ])
    def test_color_without_material(self, color, lightPos, lightAmbient,
                                    expected):
        plane = self._plane(color=color)
        light = self._light(lightPos, ambient=lightAmbient)
        frame = self._render(plane, [light])
        self._assertColor(self._pixel(frame), expected)

    def test_shading_without_material(self):
        # stimuli without a material are still shaded by lights
        sphere = SphereStim(
            self.win, radius=1.0, pos=(0, 0, -3), color=(1, 1, 1))
        frame = self._render(sphere, [self._light((1, 0, 0))])
        lit = self._pixel(frame, 0.3, 0)
        dark = self._pixel(frame, -0.3, 0)
        assert lit.sum() > dark.sum() + 3 * 50, (lit, dark)

    @pytest.mark.parametrize('sceneAmbient, expected', [
        ((0, 0, 0), (0, 0, 0)),
        ((.5, .5, .5), (128, 0, 0)),
    ])
    def test_use_lights_disabled_without_material(self, sceneAmbient,
                                                  expected):
        # as with materials, lights have no effect unless `useLights` is set,
        # only the scene ambient light is used, the same as without lights
        plane = self._plane(color=(1, -1, -1))
        frame = self._render(
            plane, [self._light((0, 0, 1))], sceneAmbient=sceneAmbient,
            useLights=False)
        self._assertColor(self._pixel(frame), expected)

        noLights = self._render(plane, sceneAmbient=sceneAmbient)
        self._assertColor(self._pixel(noLights), expected)


class TestStim3DTextureMapping(_Stim3DRenderTest):
    """Tests for mapping textures onto 3D stimuli.

    Stimuli use a white material with a texture whose quadrants are different
    colors, lit straight on by a white light so drawn colors match the texture.
    """

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)

    @pytest.fixture
    def textureFile(self, tmp_path):
        """Image file with red, green, blue and yellow quadrants (top-left,
        top-right, bottom-left and bottom-right).
        """
        size = 64
        half = size // 2
        im = np.zeros((size, size, 3), dtype=np.uint8)
        im[:half, :half] = self.RED  # rows go from top to bottom
        im[:half, half:] = self.GREEN
        im[half:, :half] = self.BLUE
        im[half:, half:] = self.YELLOW

        path = tmp_path / 'quadrants.png'
        Image.fromarray(im).save(path)
        return path

    @pytest.fixture
    def texture(self, textureFile):
        return gt.createTexImage2dFromFile(str(textureFile))

    def _quadrantColor(self, u, v):
        """Expected color at texture coordinates (u, v), where (0, 0) is the
        bottom-left of the image and the texture repeats outside 0 to 1.
        """
        right = u % 1. >= 0.5
        top = v % 1. >= 0.5
        if top:
            return self.GREEN if right else self.RED
        return self.YELLOW if right else self.BLUE

    def _texturedMaterial(self, texture):
        material = BlinnPhongMaterial(
            self.win, diffuseColor=(1, 1, 1), specularColor=(-1, -1, -1),
            ambientColor=(-1, -1, -1), emissionColor=(-1, -1, -1))
        material.diffuseTexture = texture
        return material

    def _renderLit(self, stim):
        """Draw `stim` lit by a white light shining from the viewer."""
        light = LightSource(
            self.win, pos=(0, 0, 1), lightType='directional',
            diffuseColor=(1, 1, 1), specularColor=(-1, -1, -1),
            ambientColor=(-1, -1, -1))
        return self._render(stim, [light])

    def _sample(self, frame, point):
        """Color of the pixel showing `point` in the scene."""
        return self._pixel(frame, *self._project(point))

    # --------------------------------------------------------------------------
    # Planes
    #

    def test_plane_orientation(self, texture):
        # the image appears upright, the same way round as in the file
        plane = PlaneStim(self.win, size=(1, 1), pos=(0, 0, -3))
        plane.material = self._texturedMaterial(texture)
        frame = self._renderLit(plane)

        for x, y, expected in [(-.25, .25, self.RED), (.25, .25, self.GREEN),
                               (-.25, -.25, self.BLUE),
                               (.25, -.25, self.YELLOW)]:
            self._assertColor(self._sample(frame, (x, y, -3)), expected)

    @pytest.mark.parametrize('angle', [90, 180, 270])
    def test_plane_rotation(self, texture, angle):
        # the texture turns with the plane
        plane = PlaneStim(self.win, size=(1, 1), pos=(0, 0, -3))
        plane.material = self._texturedMaterial(texture)
        plane.setOriAxisAngle((0, 0, 1), angle)
        frame = self._renderLit(plane)

        c, s = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        for x, y in [(-.25, .25), (.25, .25), (-.25, -.25), (.25, -.25)]:
            # position of the texture point after rotating the plane
            point = (c * x - s * y, s * x + c * y, -3)
            expected = self._quadrantColor(x + .5, y + .5)
            self._assertColor(self._sample(frame, point), expected)

    @pytest.mark.parametrize(
        'textureScale', [1, 2, 3, (2, 1), (1, 3)], ids=str)
    def test_plane_texture_scale(self, texture, textureScale):
        # the texture repeats `textureScale` times across the plane
        plane = PlaneStim(
            self.win, size=(1, 1), pos=(0, 0, -3), textureScale=textureScale)
        plane.material = self._texturedMaterial(texture)
        frame = self._renderLit(plane)

        su, sv = np.broadcast_to(textureScale, (2,))
        # sample the center of each quadrant of each repeat
        for i in range(2 * su):
            for j in range(2 * sv):
                x = (i + .5) / (2 * su) - .5
                y = (j + .5) / (2 * sv) - .5
                expected = self._quadrantColor((x + .5) * su, (y + .5) * sv)
                self._assertColor(self._sample(frame, (x, y, -3)), expected)

    def test_load_without_transpose(self, textureFile):
        # without flipping, image rows are in the opposite order to OpenGL's
        # so the image appears upside down
        texture = gt.createTexImage2dFromFile(str(textureFile), transpose=False)
        plane = PlaneStim(self.win, size=(1, 1), pos=(0, 0, -3))
        plane.material = self._texturedMaterial(texture)
        frame = self._renderLit(plane)

        self._assertColor(self._sample(frame, (-.25, .25, -3)), self.BLUE)
        self._assertColor(self._sample(frame, (.25, -.25, -3)), self.GREEN)

    # --------------------------------------------------------------------------
    # Other shapes
    #

    @pytest.mark.parametrize('axis, angle', [
        ((0, 1, 0), 0),     # +Z face
        ((0, 1, 0), 90),    # -X face
        ((0, 1, 0), 180),   # -Z face
        ((0, 1, 0), -90),   # +X face
        ((1, 0, 0), 90),    # +Y face
        ((1, 0, 0), -90),   # -Y face
    ])
    def test_box_faces(self, texture, axis, angle):
        # each face shows the whole texture
        box = BoxStim(self.win, size=(1, 1, 1), pos=(0, 0, -3))
        box.material = self._texturedMaterial(texture)
        box.setOriAxisAngle(axis, angle)
        frame = self._renderLit(box)

        # quadrant centers of the face towards the viewer
        samples = [tuple(self._sample(frame, (x, y, -2.5)))
                   for x, y in [(-.25, .25), (.25, .25), (-.25, -.25),
                                (.25, -.25)]]
        for sample in samples:
            assert any(np.all(np.abs(np.subtract(sample, c)) <= self.TOL)
                       for c in (self.RED, self.GREEN, self.BLUE, self.YELLOW)
                       ), sample
        assert len(set(samples)) == 4, samples

    def test_box_front_orientation(self, texture):
        box = BoxStim(self.win, size=(1, 1, 1), pos=(0, 0, -3))
        box.material = self._texturedMaterial(texture)
        frame = self._renderLit(box)

        for x, y, expected in [(-.25, .25, self.RED), (.25, .25, self.GREEN),
                               (-.25, -.25, self.BLUE),
                               (.25, -.25, self.YELLOW)]:
            self._assertColor(self._sample(frame, (x, y, -2.5)), expected)

    @pytest.mark.parametrize('axis, angle', [
        ((1, 0, 0), 0),    # a pole facing the viewer
        ((1, 0, 0), -90),  # poles at the top and bottom
    ])
    def test_sphere(self, texture, axis, angle):
        # the poles of the sphere are on its Z axis. Texture `u` goes around
        # the poles, `v` goes from the +Z pole (0) to the -Z pole (1).
        sphere = SphereStim(self.win, radius=1.0, pos=(0, 0, -3))
        sphere.material = self._texturedMaterial(texture)
        sphere.setOriAxisAngle(axis, angle)
        frame = self._renderLit(sphere)
        toLocal = sphere.thePose.inverseModelMatrix

        quadrants = [self.RED, self.GREEN, self.BLUE, self.YELLOW]

        def closestQuadrant(sample):
            # lighting darkens the sphere away from its center, so compare
            # hues rather than values
            similarity = [np.dot(sample, c) / np.linalg.norm(c)
                          for c in quadrants]
            return quadrants[int(np.argmax(similarity))]

        nChecked = 0
        for x in np.linspace(-.6, .6, 7):
            for y in np.linspace(-.6, .6, 7):
                if x ** 2 + y ** 2 > .6 ** 2:
                    continue
                # point on the surface of the sphere, in the sphere's frame
                point = (x, y, -3 + np.sqrt(1 - x ** 2 - y ** 2))
                lx, ly, lz = np.matmul(toLocal, np.append(point, 1.))[:3]
                u = 1. - (np.arctan2(ly, lx) % (2 * np.pi)) / (2 * np.pi)
                v = (np.pi / 2 - np.arcsin(np.clip(lz, -1, 1))) / np.pi

                # skip points near quadrant edges, where colors are blended
                if (min(abs(u - .5), u, 1 - u) < .05 or
                        abs(v - .5) < .05):
                    continue

                sample = self._sample(frame, point)
                assert closestQuadrant(sample) == self._quadrantColor(u, v), \
                    ((x, y), (u, v), sample)
                nChecked += 1

        assert nChecked >= 10

    def test_obj_mtl_texture(self, tmp_path, textureFile):
        # textures in the MTL file are loaded with the materials
        objFile = _writeObjFile(tmp_path)
        (tmp_path / 'cube.mtl').write_text(
            'newmtl red\nNs 10\nKa 0 0 0\nKd 1 1 1\nKs 0 0 0\n'
            'map_Kd {0}\n\n'
            'newmtl blue\nNs 10\nKa 0 0 0\nKd 1 1 1\nKs 0 0 0\n'
            'map_Kd {0}\n'.format(textureFile.name))

        stim = ObjMeshStim(self.win, str(objFile), pos=(0, 0, -3))
        assert stim.material['red'].diffuseTexture is not None
        # the same file is only loaded once
        assert (stim.material['red'].diffuseTexture is
                stim.material['blue'].diffuseTexture)

        # the OBJ is a box, so faces are mapped the same as `BoxStim`
        frame = self._renderLit(stim)
        for x, y, expected in [(-.25, .25, self.RED), (.25, .25, self.GREEN),
                               (-.25, -.25, self.BLUE),
                               (.25, -.25, self.YELLOW)]:
            self._assertColor(self._sample(frame, (x, y, -2.5)), expected)


class TestWindowMouseRay(_Stim3DRenderTest):
    """Tests for `Window.getMouseRay` and `Window.coordToRay`."""

    def teardown_method(self):
        self.win.units = 'norm'
        self.win.resetEyeTransform()

    def _toWindowUnits(self, ndc, units):
        """Convert normalized device coordinates to window units."""
        bufferPix = np.asarray(ndc[:2]) * self.win.size / 2.
        if units == 'norm':
            return np.asarray(ndc[:2])
        elif units == 'pix':  # half the framebuffer resolution on Retina
            return bufferPix / (2. if self.win.useRetina else 1.)
        elif units == 'height':
            return bufferPix / self.win.size[1]

    @staticmethod
    def _distanceToRay(point, rayOrig, rayDir):
        toPoint = np.subtract(point, rayOrig)
        return np.linalg.norm(toPoint - np.dot(toPoint, rayDir) * rayDir)

    @pytest.mark.parametrize('units', ['norm', 'pix', 'height'])
    def test_ray_through_point(self, units):
        # a ray through where a point appears in the window passes through the
        # point
        self.win.units = units
        self.win.setPerspectiveView()
        eyePos = np.linalg.inv(self.win.viewMatrix)[:3, 3]

        for point in [(0., 0., -3.), (.5, -.25, -2.), (-1., .75, -4.)]:
            ndc = vt.pointToNdc(
                point, self.win.viewMatrix, self.win.projectionMatrix)
            rayOrig, rayDir = self.win.getMouseRay(
                self._toWindowUnits(ndc, units))

            assert np.allclose(rayOrig, eyePos, atol=1e-5)
            assert np.isclose(np.linalg.norm(rayDir), 1.)
            assert self._distanceToRay(point, rayOrig, rayDir) < 1e-4, point
            assert np.dot(np.subtract(point, rayOrig), rayDir) > 0  # in front

    def test_ray_view_matrix(self):
        # rays start at the viewer and follow the direction it's looking
        self.win.setPerspectiveView()
        camera = mt.RigidBodyPose((1., 2., 3.))
        camera.alignTo((0., 0., -3.))
        self.win.viewMatrix = camera.getViewMatrix()

        rayOrig, rayDir = self.win.getMouseRay((0, 0))
        assert np.allclose(rayOrig, camera.pos, atol=1e-5)
        assert np.allclose(rayDir, mt.normalize(np.subtract((0, 0, -3), camera.pos)),
                           atol=1e-5)

    def test_ray_from_mouse(self):
        # without a position, the ray goes through the mouse
        self.win.setPerspectiveView()
        handle = self.win.winHandle
        for x, y in [(10, 20), (100, 40)]:
            handle._mouse_x, handle._mouse_y = x, y
            mousePos = self.win._mouse.getPos()
            for a, b in zip(self.win.getMouseRay(),
                            self.win.getMouseRay(mousePos)):
                assert np.allclose(a, b)

    def test_ray_orthographic(self):
        # rays are parallel for orthographic projections, starting from the
        # point under the position on the near clipping plane
        self.win.resetEyeTransform()
        rays = [self.win.getMouseRay(pos)
                for pos in [(0., 0.), (.5, -.5), (-.25, .75)]]
        for pos, (rayOrig, rayDir) in zip([(0., 0.), (.5, -.5), (-.25, .75)],
                                          rays):
            assert np.allclose(rayDir, rays[0][1])
            ndc = vt.pointToNdc(
                rayOrig, self.win.viewMatrix, self.win.projectionMatrix)
            assert np.allclose(ndc[:2], pos, atol=1e-5)

    @pytest.mark.parametrize('units', ['norm', 'pix', 'height'])
    def test_coordToRay(self, units):
        # without rotating the view, the ray relative to the viewer has the
        # same direction as in the scene
        self.win.units = units
        self.win.setPerspectiveView()
        for ndc in [(0., 0.), (.5, 0.), (-.5, .5)]:
            pos = self._toWindowUnits(ndc, units)
            _, rayDir = self.win.getMouseRay(pos)
            assert np.allclose(self.win.coordToRay(pos), rayDir, atol=1e-5)

    def test_ray_picks_stimulus(self):
        sphere = SphereStim(self.win, radius=.5, pos=(0., 0., -3.))
        self.win.setPerspectiveView()

        # the center of the window is over the sphere, the corner isn't
        rayOrig, rayDir = self.win.getMouseRay((0., 0.))
        hit = sphere.getRayIntersectSphere(rayOrig, rayDir)
        assert hit is not None
        assert np.allclose(hit[0], (0., 0., -2.5), atol=1e-5)
        assert sphere.getRayIntersectSphere(
            *self.win.getMouseRay((.95, .95))) is None


if __name__ == '__main__':
    pytest.main([__file__])
