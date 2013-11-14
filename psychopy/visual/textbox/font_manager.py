# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 12:18:45 2013

@author: Sol
"""
import os
        
class SystemFontManager(object):
    freetype_import_error=None
    def __init__(self,monospace_only=True):
        if SystemFontManager.freetype_import_error:
            raise Exception('Appears the freetype library could not load. Error: %s'%(str(SystemFontManager.freetype_import_error)))
        self.font_family_styles=[]
        self._sys_font_info={}
        self.updateSystemFontInfo(monospace_only)
        
    def updateSystemFontInfo(self,monospace_only=True):
        self._sys_font_info.clear()
        del self.font_family_styles[:]
        import matplotlib.font_manager as font_manager    
        font_paths=font_manager.findSystemFonts()

        def createFontInfo(fp,fface):
            fns=(fface.family_name,fface.style_name)
            if fns in self.font_family_styles:
                pass
            else:
                self.font_family_styles.append((fface.family_name,fface.style_name))
            
            fface.style_name
            styles_for_font_dict=self._sys_font_info.setdefault(fface.family_name,{})
            fonts_for_style=styles_for_font_dict.setdefault(fface.style_name,[])
            fonts_for_style.append(FontInfo(fp,fface))
            
        for fp in  font_paths:
            if os.path.isfile(fp) and os.path.exists(fp):
                face=Face(fp)
                if monospace_only:
                    if face.is_fixed_width:
                        createFontInfo(fp,face)
                else:
                    createFontInfo(fp,face)

        self.font_family_styles.sort() 
               
    def getFontFamilyStyles(self):
        return self.font_family_styles
        
    def getSystemFontInfo(self,refresh=False,monospace=True):
        if refresh or not self._sys_font_info:
            self.updateSystemFontInfo(monospace)
        return self._sys_font_info

    def getFontFamilyNames(self):
        return self._sys_font_info.keys()
        
    def getFontStylesForFamily(self,family_name):
        style_dict= self._sys_font_info.get(family_name)
        if style_dict:
            return style_dict.keys()

    def getFontsMatching(self,font_family_name,bold=False,italic=False,font_style=None):
        style_dict=self._sys_font_info.get(font_family_name)
        if style_dict is None:
            return None
        if font_style and font_style in style_dict.keys():
            return style_dict[font_style]
        for style,fonts in style_dict.iteritems():
            b,i=self.booleansFromStyleName(style)
            if b==bold and i==italic:
                return fonts
        return None

    def booleansFromStyleName(self,style):
        """
        For the given style name, return a
        bool indicating if the font is bold, and a second indicating
        if it is italics.
        """
        italic=False
        bold=False
        s=style.lower().strip()
        if s == 'regular':
            return False, False
        if s.find('italic')>=0 or s.find('oblique')>=0:
            italic=True    
        if s.find('bold')>=0:
            bold=True    
        return bold,italic
        
class FontInfo(object):
    def __init__(self,fp,face):
        self.path=fp
        self.family_name=face.family_name
        self.style_name=face.style_name
        self.charmaps=[charmap.encoding_name for charmap in face.charmaps]
        self.num_faces=face.num_faces
        self.size_info= [dict(width=s.width,height=s.height,x_ppem=s.x_ppem,y_ppem=s.y_ppem) for s in face.available_sizes]
        self.units_per_em=face.units_per_EM
        self.monospace=face.is_fixed_width
        self.label="%s_%s"%(face.family_name,face.style_name)
        
    def asdict(self):
        return dict(path=self.path,family_name=self.family_name,
                   style_name=self.style_name,charmaps=self.charmaps,
                   num_faces=self.num_faces,size_info=self.size_info,
                   units_per_em=self.units_per_em,monospace=self.monospace)

    def loadFont(self):
        return Face(self.path)

try:
    from psychopy.visual.textbox.freetype_bf import Face
except Exception, e:
    SystemFontManager.freetype_import_error=e

