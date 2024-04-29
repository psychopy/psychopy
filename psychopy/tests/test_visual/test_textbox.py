from pathlib import Path

import numpy as np

from psychopy import layout
from psychopy.alerts._errorHandler import _BaseErrorHandler
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin, _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy.visual import Window
from psychopy.visual import TextBox2
from psychopy.tools.fontmanager import FontManager
import pytest
from psychopy.tests import utils

# cd psychopy/psychopy
# py.test -k textbox --cov-report term-missing --cov visual/textbox


@pytest.mark.textbox
class Test_textbox(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin):
    def setup_method(self):
        self.win = Window((128, 128), pos=(50, 50), monitor="testMonitor", allowGUI=False, autoLog=False)
        self.error = _BaseErrorHandler()
        self.textbox = TextBox2(self.win,
                                "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question.",
                                placeholder="Placeholder text",
                                font="Noto Sans", alignment="top left", lineSpacing=1, padding=0.05,
                                pos=(0, 0), size=(1, 1), units='height',
                                letterHeight=0.1, colorSpace="rgb")
        self.obj = self.textbox  # point to textbox for mixin tests
        # Pixel which is the border color
        self.borderPoint = (0, 0)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (2, 2)
        self.fillUsed = True
        # Textbox foreground is too unreliable due to fonts for pixel analysis
        self.foreUsed = False

    def teardown_method(self):
        self.win.close()

    def test_glyph_rendering(self):
        # Prepare textbox
        self.textbox.colorSpace = 'rgb'
        self.textbox.color = 'white'
        self.textbox.fillColor = (0, 0, 0)
        self.textbox.borderColor = None
        self.textbox.opacity = 1

        # Add all Noto Sans fonts to cover widest possible base of handles characters
        for font in ["Noto Sans", "Noto Sans HK", "Noto Sans JP", "Noto Sans KR", "Noto Sans SC", "Noto Sans TC", "Niramit", "Indie Flower"]:
            self.textbox.fontMGR.addGoogleFont(font)
        # Some exemplar text to test basic TextBox rendering
        exemplars = [
            # An English pangram
            {"text": "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question.",
             "font": "Noto Sans", "size": 16,
             "screenshot": "exemplar_1.png"},
            # The same pangram in IPA
            {"text": "ə saɪkəʊpaɪ zɛlət nəʊz ə smidge ɒv wx, bʌt ˈʤɑːvəskrɪpt ɪz ðə ˈkwɛsʧən",
                "font": "Noto Sans", "size": 16,
                "screenshot": "exemplar_2.png"},
            # The same pangram in Hangul
            {"text": "아 프시초피 제알롣 크노W스 아 s믿게 오f wx, 붇 자v앗c립t 잇 테 q왯디온",
             "font": "Noto Sans KR", "size": 16,
             "screenshot": "exemplar_3.png"},
            # A noticeably non-standard font
            {"text": "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question.",
             "font": "Indie Flower", "size": 16,
             "screenshot": "exemplar_4.png",
            }
        ]
        # Some text which is likely to cause problems if something isn't working
        tykes = [
            # Text which doesn't render properly on Mac (Issue #3203)
            {"text": "कोशिकायें",
             "font": "Noto Sans", "size": 16,
             "screenshot": "tyke_1.png"},
            # Thai text which old Text component couldn't handle due to Pyglet
            {"text": "ขาว แดง เขียว เหลือง ชมพู ม่วง เทา",
             "font": "Niramit", "size": 16,
             "screenshot": "tyke_2.png"
             },
            # Text which had the top cut off
            {"text": "โฬิปื้ด็ลู",
             "font": "Niramit", "size": 36,
             "screenshot": "cutoff_top.png"},
        ]
        # Test each case and compare against screenshot
        for case in exemplars + tykes:
            self.textbox.reset()
            self.textbox.fontMGR.addGoogleFont(case['font'])
            self.textbox.letterHeight = layout.Size(case['size'], "pix", self.win)
            self.textbox.font = case['font']
            self.textbox.text = case['text']
            self.win.flip()
            self.textbox.draw()
            if case['screenshot']:
                # Uncomment to save current configuration as desired
                filename = "textbox_{}_{}".format(self.textbox._lineBreaking, case['screenshot'])
                #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)

    def test_colors(self):
        # Do base tests
        _TestColorMixin.test_colors(self)
        # Do own custom tests
        self.textbox.text = "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question."
        # Some exemplar text to test basic colors
        exemplars = [
            # White on black in rgb
            {"color": (1, 1, 1), "fillColor": (-1,-1,-1), "borderColor": (-1,-1,-1), "space": "rgb",
             "screenshot": "colors_WOB.png"},
            # White on black in named
            {"color": "white", "fillColor": "black", "borderColor": "black", "space": "rgb",
             "screenshot": "colors_WOB.png"},
            # White on black in hex
            {"color": "#ffffff", "fillColor": "#000000", "borderColor": "#000000", "space": "hex",
             "screenshot": "colors_WOB.png"},
            {"color": "red", "fillColor": "yellow", "borderColor": "blue", "space": "rgb",
             "screenshot": "colors_exemplar1.png"},
            {"color": "yellow", "fillColor": "blue", "borderColor": "red", "space": "rgb",
             "screenshot": "colors_exemplar2.png"},
            {"color": "blue", "fillColor": "red", "borderColor": "yellow", "space": "rgb",
             "screenshot": "colors_exemplar3.png"},
        ]
        # Some colors which are likely to cause problems if something isn't working
        tykes = [
            # Text only
            {"color": "white", "fillColor": None, "borderColor": None, "space": "rgb",
             "screenshot": "colors_tyke1.png"},
            # Fill only
            {"color": None, "fillColor": "white", "borderColor": None, "space": "rgb",
             "screenshot": "colors_tyke2.png"},
            # Border only
            {"color": None, "fillColor": None, "borderColor": "white", "space": "rgb",
            "screenshot": "colors_tyke3.png"},
        ]
        # Test each case and compare against screenshot
        for case in exemplars + tykes:
            # Raise error if case spec does not contain all necessary keys
            if not all(key in case for key in ["color", "fillColor", "borderColor", "space", "screenshot"]):
                raise KeyError(f"Case spec for test_colors in class {self.__class__.__name__} ({__file__}) invalid, test cannot be run.")
            # Apply params from case spec
            self.textbox.colorSpace = case['space']
            self.textbox.color = case['color']
            self.textbox.fillColor = case['fillColor']
            self.textbox.borderColor = case['borderColor']
            for lineBreaking in ('default', 'uax14'):
                self.win.flip()
                self.textbox.draw()
            if case['screenshot']:
                # Uncomment to save current configuration as desired
                filename = "textbox_{}_{}".format(self.textbox._lineBreaking, case['screenshot'])
                # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)

    def test_char_colors(self):
        cases = [
            # Named color
            {'text': "<c=white>Hello</c> there",
             'space': "rgb",
             'base': "black",
             'screenshot': "white_hello_black_there"},
            # Hex color
            {'text': "<c=#ffffff>Hello</c> there",
             'space': "rgb",
             'base': "black",
             'screenshot': "white_hello_black_there"},
            # RGB color
            {'text': "<c=(1, 1, 1)>Hello</c> there",
             'space': "rgb",
             'base': "black",
             'screenshot': "white_hello_black_there"},
            # RGB255 color
            {'text': "<c=(255, 255, 255)>Hello</c> there",
             'space': "rgb255",
             'base': "black",
             'screenshot': "white_hello_black_there"},
            # Rainbow
            {'text': (
                "<c=red>R</c><c=orange>o</c><c=yellow>y</c> <c=green>G.</c> "
                "<c=blue>B</c><c=indigo>i</c><c=violet>v</c> is a colorful man and he proudly stands at "
                "the rainbow's end"
            ),
                'space': "rgb",
                'base': "white",
                'screenshot': "roygbiv"},
        ]

        for case in cases:
            # Set attributes from test cases
            self.textbox.colorSpace = case['space']
            self.textbox.color = case['base']
            self.textbox.text = case['text']
            # Draw
            self.win.flip()
            self.textbox.draw()
            # Compare screenshot
            filename = "textbox_charcolors_{}_{}.png".format(self.textbox._lineBreaking, case['screenshot'])
            #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=20)

    def test_caret_position(self):

        # Identify key indices to test
        indices = (
            4,  # first line
            30,  # wrapping line
            64  # newline line
        )
        # One array for anchor and alignment as they use the same allowed vals
        anchalign = (
            'center',
            'top-center',
            'bottom-center',
            'center-left',
            'center-right',
            'top-left',
            'top-right',
            'bottom-left',
            'bottom-right',
        )
        # Try with all anchors
        for anchor in anchalign:
            # Try with all alignments
            for align in anchalign:
                # Try flipped horiz and unflipped
                for flipHoriz in (True, False):
                    # Try flipped vert and unflipped
                    for flipVert in (True, False):
                        # Create a textbox with multiple lines of differing length from both wrapping and a newline char
                        textbox = TextBox2(
                            self.win,
                            text="A PsychoPy zealot knows a smidge of wx, but JavaScript is the \nquestion.",
                            size=(128, 64), pos=(0, 0), units='pix',
                            anchor=anchor, alignment=align, flipHoriz=flipHoriz, flipVert=flipVert
                        )
                        # Check that caret position at key indices matches character positions
                        for i in indices:
                            # Set caret index
                            textbox.caret.index = i
                            # Draw textbox to refresh verts
                            textbox.draw()
                            textbox.caret.draw()
                            # Compare bottom vert of caret to bottom right vert of character (within 1 px)
                            caretVerts = textbox.caret.vertices
                            charVerts = textbox._vertices.pix[range((i-1) * 4, (i-1) * 4 + 4)]
                            assert all(np.isclose(caretVerts[0], charVerts[2], 1)), (
                                f"Textbox caret at index {i} didn't align with bottom right corner of "
                                f"matching char when:\n"
                                f"anchor={anchor}, alignment={align}, flipHoriz={flipHoriz}, flipVert={flipVert}.\n"
                                f"Caret vertices were:\n"
                                f"{caretVerts}\n"
                                f"Char verts were \n"
                                f"{charVerts}\n"
                            )

    def test_typing(self):
        """Check that continuous typing doesn't break anything"""
        # Make sure the textbox has the right colours
        self.textbox.color = "white"
        self.textbox.fillColor = None
        self.textbox.borderColor = None
        # Make textbox editable
        wasEditable = self.textbox.editable
        self.textbox.editable = True
        # Define some cases
        exemplars = [
            {"text": "",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_blank.png"},  # No text
            {"text": "test←←←←",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_blank.png"},  # Make some text then delete it
            {"text": "A PsychoPy zealot knows a smidge of wx, but JavaScript is the question.",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_pangram.png"},  # Pangram
            {"text": "ther◀◀◀◀Hello ▶▶▶▶e",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_navLR.png"},  # Try moving left/rght
            {"text": "Hello←o there←e◀◀◀→e",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_navDel.png"},  # Try backspace/delete
            {"text": "Hello\nthere",
             "font": "Noto Sans",
             "screenshot": "textbox_typing_newline.png"},  # Try with a new line
        ]
        tykes = [
            # {
            #     "text": "엹 씨쓹촜 둪 캡탃뉸퀑띱 땀 젲깷굨텕하성쪟 뗸엦붊즈눂죿헶맕흁 윸끱뫏폒튯븇  땪샒죳웘핱 쑁뻸귣퀤늾녻늈냽쉜늌륝씑혅앴 잏 콡뒘  ᇵ쮣둿녩욀범 ᇖ됶쟤햔쬷쓃늅뤛섳퉃  킡 쎺뫙썛륆  뇲 짭 핫챦 켘횧뤠휦뺵촯끙  푓킘 휳잛딀꼄죘 텏룧쟨솎쿍 캋앦 ᆲ뙝뎛 낀 멟칾랟녇뙥쐊 쬻틇듥 듫엮씡붞 겡 뽕 썦썓  땤껪픐뫾툆폅륿캯 멄퇓뱫쫵 쪊쁐   픍풼뺖샷  묚볥 쟃 국땗푋믋쬩륶쩔꽆겋럛귛뤄랳 랧뉄쓠떸 놲 낟싸쑆썹 옰겏 듇쏮 쭟 럕룚뮤급윲흹뤙셄뒴뷃쁯큹뵫 톤싟뽰뾆ᆛ탠촻퀘퇅휙뚘팛모찈툣귟뺕쬸뻜 뉭뱳튯뉸 봯즉젊 령즼넃훵쏂쿼좷힆펯좲췟럥쿮 묘퀱녌됮퀟뀲텚뾠퐂놆틷궞몶챁뤩깜쉺톚 쿄빈궁  끵쿤쵨슳벥풂걊뮽 찪 볼 윚곭쑒촢ᄯ뛺 롄틴얕쫻쪠랼묥륾걅쁄퍱쨍액쩕 꽇텳쌔꺓끮봛굔쿻칡훳쒹촲볂댘얄떸밢극뿩뉳 툲굹 갰삭 첁긇꿊댠퉄캫옵즈새륳뷂봇쁆겈럵ᆬ 쓝쯙뙶벗덆뛫걾캆놫왛젂밃힑뜾뱝듉뾱껆펢끽룓 뛓 퍯볍 뵁ᇉᆚ슙 봉ᅧ민픋귲컬쵾찁뵜쇃츻ᇶ띉  쬢홀촑뇢폯  뼻릯쵊 뎴딆 퉁섀벌즿앀 몴  틮 뤗뵱  뉋쐤얇양뜴꽫 껣룮ᇂ쭉울횰  쌀툛ᄵ쉰떩쑉틱꾽횧 퐍 뙿쀎붎쳧풃멩짓뭼  봜꼦 팘둅났 ᅛ꽷쬣 믾뺠뼯쨵둎퀲캢츤절쳴 땏 깦픦힗섙  웫윆읨콭믰뀭턟쨁 쫺즽륉팂쎴 돔쪏ᆽ뿚쮩넶쥲꼱튪떍꼽 칤   튉쉷턏 첫냮됏뢤 퇘촷펆뒲팀 좊강껽옳팠숷촑뗻 랓톀 녥쌐껙 짱뚦  쇯럶브  핛 퀪뷌살턴쫕쯌헥횚픥쾅슅옉떓듻쁡꾛싟쇑뺦긜땨혽 꽬 곞쉮 쟮딦햰 뱣롱뢓튜귪땟붖  먻룃쬿쎇랍꺽핊줌켝뙩쪜럵먨녆뚨퀈깋눷떵꿛한  풪컳멸뉉썛땸캭닊걵탞 샋훪떗묭젽븀릑ᇇ웿랯튇 슌별뉅켮얤롲펫뉋흖굈렷뚞 즥쌬꾪셼쟌뽪텛쁗쨳 꺌퍎졮츑 웳 돛빳땭펃륄 쀣 씍측 뗗꿢줋쿲삙퇖쵤놻컝붐닆싷쒓킏냆뢣과캢큘랝뫖림롦쓬싡볍킍쾃숢힂덁껖녷흂냇꽙빸꼿졗밭똒ᆿ핮럹펏 풰럗쬻뾦겡톟쫱퐄슩겧솵꾔굛퉚읚왒븚얞놨껭뭨딃욵릡흇쟗콡롡뢈펞픤촀엞  퇙땨밹귥직턣탂탂큨뽇ᄞ숀턢쁻츕 샼졒쁷웚퀭엡겙 끴컍 뱟쯮뉖펼읲뛓꿢쿤쟢얫 쟳랷ᅵ눙뫂  늚 냋츤킓팝꿂윮쥮힓윾럯턏몄픮뙜컉꼕폄 좁쇋쳠딃좡슦췃킙옅얷쇇짗탻뮏곞킣능쁕췉챖집됂 클똁 뒦잳층먯ᄁ쪂 쥄겸 굇넢뛞 맶췠챳츖귦뤔솀엸빲뾎뫜냃겱낾뭾뮑  뙹갾뗪뱐두ᄇ겈꿂솫 쎎뿽  얓믡썕췠핁혎 ᆆ헮륎촀몭덙쨄딀쵂 볋쭨볃 볌휣ᇣ ᆫ킩쪕햭퇽멂볾쵁 똺넡뗨잺 뵁귓퐽멪뽪 횉 쥋궾셺벊녁밊 ",
            #     "font": "Noto Sans KR",
            #     "screenshot": "textbox_typing_longKoeran.png"
            # },  # https://discourse.psychopy.org/t/textbox2-crashes-when-korean-input-exceed-certain-length/22717/6
            {
                "text": "i need a word which will go off the page, antidisestablishmentarianism is a very long word",
                "font": "Open Sans",
                "screenshot": "textbox_typing_longWord.png"
            },  # Check that lines wrap correctly when there's a very long word, rather than as described in https://github.com/psychopy/psychopy/issues/3892
        ]
        for case in exemplars + tykes:
            self.textbox.font = case['font']
            self.textbox.text = ""
            for letter in case['text']:
                # Handle cursor key placeholders
                if letter == '◀':
                    self.textbox._onCursorKeys('MOTION_LEFT')
                elif letter == '▶':
                    self.textbox._onCursorKeys('MOTION_RIGHT')
                elif letter == '←':
                    self.textbox._onCursorKeys('MOTION_BACKSPACE')
                elif letter == '→':
                    self.textbox._onCursorKeys('MOTION_DELETE')
                else:
                    # Input text
                    self.textbox._onText(letter)
                self.textbox.draw()
                self.win.flip()
            if case['screenshot']:
                self.win.flip()
                self.textbox.draw()
                # Force caret to draw for consistency
                self.textbox.caret.draw(override=True)
                #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / case['screenshot'])
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / case['screenshot'], self.win, crit=20)

        # Set editable back to start value
        self.textbox.editable = wasEditable

    def test_basic(self):
        pass

    def test_editable(self):
        # Make textbox editable
        self.textbox.editable = True
        # Make a second textbox, which is editable from init
        textbox2 = TextBox2(self.win, "", "Noto Sans",
                                pos=(0.5, 0.5), size=(1, 1), units='height',
                                letterHeight=0.1, colorSpace="rgb", editable=True)
        # Check that both are editable children of the window
        editables = []
        for ref in self.win._editableChildren:
            editables.append(ref())  # Actualise weakrefs
        assert self.textbox in editables
        assert textbox2 in editables
        # Set current editable to textbox 1
        self.win.currentEditable = self.textbox
        # Make sure next editable is textbox 2
        self.win.nextEditable()
        assert self.win.currentEditable == textbox2
        # Make each textbox no longer editable
        self.textbox.editable = False
        textbox2.editable = False
        # Make sure they are no longer editable children of the window
        editables = []
        for ref in self.win._editableChildren:
            editables.append(ref())  # Actualise weakrefs
        assert self.textbox not in editables
        assert textbox2 not in editables
        # Cleanup
        del textbox2

    def test_alignment(self):
        # Define classic use cases
        exemplars = [
            "top left",
            "top center",
            "top right",
            "center left",
            "center center",
            "center right",
            "bottom left",
            "bottom center",
            "bottom right",
        ]
        # Some potentially problematic use cases which should be handled
        tykes = [
            "center",
            "centre",
            "centre centre",
            "someword",
            "more than two words",
        ]
        # Get intial textbox params
        initParams = {}
        for param in ["units", "fillColor", "color", "padding", "letterHeight",  "alignment", "text"]:
            initParams[param] = getattr(self.textbox, param)
        # Test
        for case in exemplars + tykes:
            for units in layout.unitTypes:
                # Setup textbox
                self.textbox.text = "A PsychoPy zealot knows a smidge of wx but JavaScript is the question."
                self.textbox.fillColor = "white"
                self.textbox.color = "black"
                self.textbox.padding = 0
                self.textbox.letterHeight = layout.Size((0, 10), units="pix", win=self.win)
                # Set test attributes
                self.textbox.units = units
                self.textbox.alignment = case
                # Draw and compare
                self.textbox.draw()
                #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / f"textbox_{self.textbox._lineBreaking}_align_{case.replace(' ', '_')}.png")
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / f"textbox_{self.textbox._lineBreaking}_align_{case.replace(' ', '_')}.png", self.win, crit=20)
                self.win.flip()
        # Reset initial params
        for param, value in initParams.items():
            setattr(self.textbox, param, value)

    def test_speechpoint(self):
        self.obj.size = (0.5, 0.5)
        self.obj.fillColor = "red"

        # Create list of points to test
        cases = [
            (-3/8, 0),
            (3/8, 0),
            (0, -3/8),
            (0, 3/8)
        ]

        for x, y in cases:
            # Prepare window
            self.win.flip()
            # Set from case
            self.obj.speechPoint = (x, y)
            # Draw
            self.obj.draw()
            # Compare screenshots
            filename = f"{self.__class__.__name__}_testSpeechpoint_{int(x*8)}ovr8_{int(y*8)}ovr8.png"
            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(filename, self.win, crit=8)

        self.obj.speechPoint = None
            
    def test_alerts(self):
        noFontTextbox = TextBox2(self.win, "", font="Raleway Dots", bold=True)
        assert (self.error.alerts[0].code == 4325)

    def test_letter_spacing(self):
        cases = (0.6, 0.8, 1, None, 1.2, 1.4, 1.6, 1.8, 2.0)

        for case in cases:
            self.win.flip()
            # Set letter spacing
            self.obj.letterSpacing = case
            # Draw
            self.obj.draw()
            # Compare
            nameSafe = str(case).replace(".", "p")
            filename = Path(utils.TESTS_DATA_PATH) / f"TestTextbox_testLetterSpacing_{nameSafe}.png"
            self.win.getMovieFrame(buffer='back').save(filename)
            utils.compareScreenshot(filename, self.win, crit=20)


def test_font_manager():
        # Create a font manager
        mgr = FontManager()
        # Check that it finds fonts which should be pre-packaged with PsychoPy in the resources folder
        assert bool(mgr.getFontNamesSimilar("Open Sans"))
        # Check that it doesn't find fonts which aren't installed as default
        assert not bool(mgr.getFontNamesSimilar("Dancing Script"))
        # Check that it can install fonts from Google
        mgr.addGoogleFont("Hanalei")
        # Check that these fonts are found once installed
        assert bool(mgr.getFontNamesSimilar("Hanalei"))


@pytest.mark.uax14
class Test_uax14_textbox(Test_textbox):
    """Runs the same tests as for Test_textbox, but with the textbox set to uax14 line breaking"""
    def setup_method(self):
        Test_textbox.setup_method(self)
        self.textbox._lineBreaking = 'uax14'
