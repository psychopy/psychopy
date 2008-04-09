/*******************************************************************************

      BITSLIB - Bits++ API

      Copyright Cambridge Research Systems : 2002

      Header File for Bits++ Software Library 7.000

      P.Symons, R.Shiells

*******************************************************************************/

#ifndef _CRS_BITS_H_INCLUDED
#define _CRS_BITS_H_INCLUDED


#define E_DISPLAYNOTOPEN -8
#define E_INTERNALERROR  -9
#define E_ALREADYOPEN    -10
#define E_DISPLAYERROR   -11
#define E_OUTOFRESOURCES -12


typedef unsigned short WORD;
typedef unsigned long DWORD;

typedef struct
{
	double a,b,c;
} bitsTRIVAL;

typedef bitsTRIVAL bitsLUTBUFFER[256];

typedef struct
{
	int  changeA;
	int  switchA;
	int  changeB;
	int  switchB;
	int  changeC;
	int  switchC;
	long counter;
} CBBOXRECORD;


/* Constants used by bitsSetVideoMode */
#define bits8BITPALETTEMODE   0x00000001  /* normal vsg mode */
#define bitsNOGAMMACORRECT    0x00004000  /* Gamma correction mode */
#define bitsGAMMACORRECT      0x00008000  /* Gamma correction mode */
#define bitsVIDEOENCODEDCOMMS 0x00080000

/* Colour space for bitsSetColourSpace and LUT functions */
#define bitsCS_RGB           3  /* RGB colour in range 0..1 */
#define bitsCS_RGBDAC        7  /* RGB Space converted into DAC range */
#define bitsCS_CURRENTSPACE  0xFFFFFFFF  /* The space set by bitsSetColourSpace */

/* Goggle state flags, used by bitsIOSetGoggles */
#define bitsGOGGLESOFF             0x0E00
#define bitsGOGGLESBOTHCLOSED      0x0C00
#define bitsGOGGLESLEFTOPEN        0x0A00
#define bitsGOGGLESRIGHTOPEN       0x0B00
#define bitsGOGGLESBOTHOPEN        0x0D00
#define bitsGOGGLESTOGGLELEFT      0x0800
#define bitsGOGGLESTOGGLERIGHT     0x0900


/* Used by GetSystemAttribute */
#define bitsCOLOURRESOLUTION     0x0001  /* Number of levels in LUT table */
#define bitsFRAMERATE            0x0002
#define bitsFRAMETIME            0x0003
#define bitsCARDTYPE             0x0015
#define bitsVIDEOMODE            0x0016
#define bitsINITIALISESTATE      0x0017
#define bitsSOFTWAREVERSION      0x0018
#define bitsCOLOURSPACE          0x001C
#define bitsNUMDIGITALOUTBITS    0x001D
#define bitsNUMDIGITALINBITS     0x001E
#define bitsSOFTINSTALLVERSION   0x001F
#define bitsSUPPORTEDVIDEOMODES  0x0020

#define bitsLUTSIZE sizeof(bitsLUTBUFFER)  /* Number of bytes in each LUT */

/* Digital bit codes used by digital I/O functions */
#define bitsDIG0  0x001
#define bitsDIG1  0x002
#define bitsDIG2  0x004
#define bitsDIG3  0x008
#define bitsDIG4  0x010
#define bitsDIG5  0x020
#define bitsDIG6  0x040
#define bitsDIG7  0x080
#define bitsDIG8  0x100
#define bitsDIG9  0x200

/* Response box open constants */
#define respCOM1   0
#define respCOM2   1
#define respCOM3   2
#define respCOM4   3
#define respCB3    8
#define respCT3    16
#define respORB10  32

/* Response box Switch positions */
#define respEMPTY  -1  /* Input buffer is empty flag */
#define respUP     -4
#define respCENTRE -5
#define respDOWN   -6

/* Response Box Buzzer tone variations */
#define respTONE0   0  /* Highest tone */
#define respTONE1   1
#define respTONE2   2
#define respTONE3   3
#define respTONE4   4
#define respTONE5   5
#define respTONE6   6
#define respTONE7   7
#define respTONE8   8
#define respTONE9   9
#define respTONE10 10
#define respTONE11 11
#define respTONE12 12
#define respTONE13 13
#define respTONE14 14
#define respTONE15 15  /* Lowest tone */

/* Response box tone lengths */
#define respSEC01 0  /* 0.1 seconds duration */
#define respSEC02 1  /* 0.2 seconds duration */
#define respSEC05 2  /* 0.5 seconds duration */
#define respSEC10 3  /* 1.0 seconds duration */

#ifdef __cplusplus
extern "C" {
#endif


/******************************************************************************\
   Initialisation and System Property Functions *******************************
\******************************************************************************/
long __stdcall bitsInit(char *Filename);

long __stdcall bitsGetSystemAttribute(DWORD Attribute);

/******************************************************************************\
   Global Setup Functions ******************************************************
\******************************************************************************/
long __stdcall bitsSetColourSpace(DWORD ColourSpace);
long __stdcall bitsSetVideoMode(DWORD ModeFlags);

/******************************************************************************\
   General functions
\******************************************************************************/
long __stdcall bitsGetTimer(void);
long __stdcall bitsResetTimer(void);

/******************************************************************************\
   Palette control Functions
\******************************************************************************/
long __stdcall bitsPaletteRead(bitsLUTBUFFER *Buffer);
long __stdcall bitsPaletteSet(DWORD StartIndex, DWORD EndIndex, bitsTRIVAL *Colour);
long __stdcall bitsPaletteWrite(bitsLUTBUFFER *Buffer, DWORD PaletteStart, DWORD Number);

/******************************************************************************\
   I/O Functions
\******************************************************************************/
long __stdcall bitsIOReadDigitalIn(void);
long __stdcall bitsIOReadDigitalOut(void);
long __stdcall bitsIOWriteDigitalOut(DWORD Data, DWORD Mask);
long __stdcall bitsIOSetGoggles(DWORD Mode);

/******************************************************************************\
   Response box functions
\******************************************************************************/
long __stdcall bitsCbboxOpen(DWORD BoxType);
long __stdcall bitsCbboxBuzzer(DWORD Period, DWORD Frequency);  /* Buzz CB1 buzzer */
long __stdcall bitsCbboxSendback(void);                         /* Ask explicitly for switch settings */
long __stdcall bitsCbboxCheck(CBBOXRECORD *C);                  /* Check if any switches have changed */
long __stdcall bitsCbboxClose(void);                            /* Reset interrupt vectors */
long __stdcall bitsCbboxFlush(void);                            /* Flush the input buffer */

/******************************************************************************\
   
\******************************************************************************/
long __stdcall bitsGetDisplayManagerVersion(char *p);
long __stdcall bitsOpenDisplay(int hParent, int AllowSingleDisplay);
void __stdcall bitsCloseDisplay(void);
long __stdcall bitsDrawDisplay(unsigned short left, unsigned short top,
  unsigned char *buf, unsigned short bx, unsigned short by);
long __stdcall bitsGetDisplayHeight(void);
long __stdcall bitsGetDisplayWidth(void);
long __stdcall bitsEnableDX8Sync(void);


#ifdef __cplusplus
}
#endif


#endif
