```

# Font Validator Report - adm1602k.ttf

Run DateTime:  Monday, February 27, 2023 5:00 PM 
Machine Name:  RFX-POS09 
Font file:  \\wsl$\Ubuntu-22.04\home\dembry\git\dse.d\fonts.d\dot-matrix-fonts\ttf\adm1602k.ttf 
I0004 The file begins with an Offset Table (file contains a single font)
I0005 Total time validating file 0:00:09 

 
--------------------------------------------------------------------------------


Index: 0, adm1602k medium, Version 001.000 , 2/27/2023


Table Tag | Table Offset | Table Length | Table Checksum 
FFTM 0x00003e50 0x0000001c 0x9e4bd419 
OS/2 0x00000158 0x00000060 0x696a8999 
cmap 0x00000288 0x0000014a 0x17877be3 
cvt  0x000003d4 0x00000004 0x00210279 
gasp 0x00003e48 0x00000008 0xffff0003 
glyf 0x000004a0 0x00003658 0x5bf6fbce 
head 0x000000dc 0x00000036 0x21a6ed7d 
hhea 0x00000114 0x00000024 0x05a501ca 
hmtx 0x000001b8 0x000000ce 0x0e0b0676 
loca 0x000003d8 0x000000c8 0x81928fc8 
maxp 0x00000138 0x00000020 0x00cd00d1 
name 0x00003af8 0x0000025e 0x28aeffce 
post 0x00003d58 0x000000ee 0x724876d4 

## General Font Information

P0011 The numTables field is non-zero 13 
P0010 The searchRange, entrySelector, and rangeShift fields are all valid
P0032 The directory entry tags are in ascending order
P0031 The directory entry tag names are valid
P0030 The directory entry table offsets are all multiples of 4
P0020 All required tables are present

W0022 Recommended table is missing VDMX 
W0022 Recommended table is missing DSIG 

    Font: Recommended table is missing

    Depending on the typeface and coverage of a font, certain tables are recommended for optimum quality. For example, the performance of a non-linear font is improved if the VDMX, LTSH, and hdmx tables are present (use the CacheTT tool to calculate these values and create these tables). Non-monospaced Latin fonts should have a kern table. A gasp table is necessary if a designer wants to influence the sizes at which grayscaling is used under Windows. A DSIG table containing a digital signature helps ensure the integrity of the font file. Etc.

    For more information, see the details about OpenType files.


P0022 No unnecessary tables are present
P0021 Tables are in optimal order

 

## FFTM

I0040 Not an OpenType table, contents not validated

 

## OS/2

E2132 The version number is invalid 4 

    OS/2: The version number is invalid

    The current version of the OS/2 table is Version 3. Versions zero (0, TrueType rev 1.5), one (1, TrueType rev 1.66), and two (2, OpenType rev 1.2) have been used previously.

    For more information, see the OS/2 table specification. 

E2127 The table length does not match the expected length for this version

    OS/2: The table length does not match the expected length for this version

    This error indicates a structural problem with the font. Structural errors may be caused by: a font tool incorrectly generating the font file; a person altering the contents of a valid font file; or some other corruption to the font file. Regenerate the font, or contact the font vendor to obtain a valid version of the font.

    For more information, see the OS/2 table specification. 

W0051 Cannot perform test due to other errors in this table OS/2 table appears to be corrupt. No further tests will be performed. 

 

## cmap

P0312 The table version number is 0
P0307 Each subtable offset is within the table
P0306 Each subtable length is within the table
P0309 The subtables are in the correct order
P0302 There are no duplicate subtables
P0308 No overlapping subtables were found
P0310 Each subtable's format number is valid
P0305 The subtable internal format appears valid PlatID = 0, EncID = 3, Fmt = 4 
P0305 The subtable internal format appears valid PlatID = 1, EncID = 0, Fmt = 0 
P0305 The subtable internal format appears valid PlatID = 3, EncID = 1, Fmt = 4 
P0301 The table contains both Apple and Microsoft subtables
P0300 Character code 240, the Apple logo, is mapped to missing glyph in cmap 1,0 (legal requirement for Microsoft fonts)

W0304 Character code 219, the euro character, is not mapped in cmap 1,0

    cmap: Character code 219, the euro character, is not mapped in cmap 1,0

    The Euro glyph is required for all Microsoft fonts. The glyph should be mapped to Unicode U+20AC, and Macintosh character code 219.

    For more information, see the cmap table specification. 

W0305 Character code U+20AC, the euro character, is not mapped in cmap 3,1

    cmap: Character code U+20AC, the euro character, is not mapped in cmap 3,1

    The Euro glyph is required for all Microsoft fonts. The glyph should be mapped to Unicode: U+20AC, and Macintosh character code: x00DB

    For more information, see the cmap table specification

P0311 No characters are mapped in the Unicode Private Use area
P0314 All non mac subtables have a language field of zero

 

## cvt 

P0400 The length of the cvt table is an even number of bytes

 

## gasp

P1003 The version number is 0
P1000 All of the rangeGaspBehavior fields contain valid flags
P1002 The gaspRange array is in sorted order
P1001 The gaspRange array has a 0xFFFF sentinel
P1004 No adjacent ranges have identical flags

 

## glyf

P1700 Correct format of loca (0 or 1)

 

## head

P1323 Table length is 54 bytes
P1324 The table version number is 0x00010000
P1330 fontRevision is consistent with the font's version string 1.000 
P1307 Font checksum is correct 0xf8707ff6 
P1321 The magic number is 0x5f0f3cf5
P1303 Non-linear scaling flag (bit 4) is clear, and hdmx table is not present
P1304 Non-linear scaling flag (bit 4) is clear, and LTSH table is not present
P1301 Reserved bit 14 of the flags field is clear
P1302 Reserved bit 15 of the flags field is clear

W1313 The unitsPerEm value is not a power of two 1000 

    head: The unitsPerEm value is not a power of two

    Microsoft and Apple recommend that the unitsPerEm value of the font is a power of 2. Such a value allows font clients to efficiently perform calculations involving division.

    Microsoft considers a value of 2048 unitsPerEm to be ideal because it is a power of 2, a high enough value for good precision in rendering, and a low enough value to be processed efficiently.

    To learn more about these recommendations, see the Hinting and Production Guidelines Specification.

    For more information, see the head table specification. 

W1301 The created time is an unlikely value created = 3760379093 (Monday, February 27, 2023 9:44 PM) 

    head: The created time is an unlikely value

    The time the font was created should be a 64-bit integer that equals the number of seconds since midnight, January 1, 1904. Use a table editing tool to correct this value.

    For more information, see the head table specification. 

W1311 The modified time is an unlikely value modified = 3760379093 (Monday, February 27, 2023 9:44 PM) 

    head: The modified time is an unlikely value

    The time the font was modified should be a 64-bit integer that equals the number of seconds since midnight, January 1, 1904. Check to ensure that the tool you are using to edit the font is producing this value correctly.

    For more information, see the head table specification. 


P1327 The xMin value matches the minimum glyph xMin xMin = 10 
P1329 The yMin value matches the minimum glyph yMin yMin = -115 
P1326 The xMax value matches the maximum glyph xMax xMax = 568 
P1328 The yMax value matches the maximum glyph yMax yMax = 865 
P1316 The macStyle bold bit matches the name table's font subfamily string
P1320 The macStyle italic bit matches the name table's font subfamily string
P1314 The macStyle bold bit matches the OS/2 fsSelection bit
P1318 The macStyle italic bit matches the OS/2 fsSelection bit
P1319 The macStyle italic bit matches the post table italic angle
P1313 The lowestRecPPEM value is in a reasonable range
P1308 The fontDirectionHint is in the range -2..2 2 
P1312 The indexToLocFormat value is 0 or 1 0 
P1311 The indexToLocFormat value matches the loca table 0 
P1309 The glyphDataFormat value is 0

 

## hhea

P1406 The table version number is 0x00010000
P1409 The Ascender value is greater than zero
P1411 The Descender is less than zero

W1401 Ascender should be less than or equal to head.yMax Ascender = 875, head.yMax = 865 

    hhea: Ascender should be less than or equal to head.yMax

    For the most consistent performance between platforms, the hhea.ascender value should be less than or equal to the head.yMax value.

    For more information, see the hhea table specification. 


W1402 Descender should be greater than or equal to head.yMin Descender = -125, head.yMin = -115 

    hhea: Descender should be greater than or equal to head.yMin

    For the most consistent performance between platforms, the hhea.descender value should be greater than or equal to the head.yMin value.

    For more information, see the hhea table specification. 


P1413 LineGap is greater than or equal to 0
P1415 Ascender is same value as OS/2.usWinAscent
P1416 Descender value is the same as OS/2.usWinDescent
P1414 The LineGap is greater to or equal the minimum recommended value
P1400 The advanceWidthMax field equals the calculated value
E1402 The minLeftSideBearing field does not equal the calculated value actual = 0, calc = 10 

    hhea: The minLeftSideBearing field does not equal the calculated value

    The value of the minLeftSideBearing field should equal the minimum left side bearing value listed in the hmtx table for glyphs with contours. Glyphs with no contours should be ignored.

    For more information, see the hhea table specification. 

E1403 The minRightSideBearing field does not equal the calculated value actual = 0, calc = 10 

    hhea: The minRightSideBearing field does not equal the calculated value

    The value of the minRightSideBearing field should equal Min(aw - lsb - (xMax - xMin)). Only glyphs with contours should be used when making this calculation. Glyphs with no contours should be ignored.

    For more information, see the hhea table specification. 

P1407 The xMaxExtent field equals the calculated value
P1405 The reserved fields are all set to zero
P1401 The metricDataFormat field is set to zero
P1404 The numberOfHMetrics value is consistent with the length of the hmtx table
P1408 The caretSlope angle matches the post.italicAngle

 

## hmtx

P1501 The size of the table matches the calculated size
P1500 The horizontal metrics are all within an allowable range of values

 

## loca

P1700 Correct format of loca (0 or 1)
P1704 The number of entries is equal to (maxp.numGlyphs + 1)
P1705 The entries are sorted in ascending order
P1706 All entries point within range of the glyf table
P1702 Loca references a glyf entry which length is not a multiple of 4
I1700 Loca references a zero-length entry in the glyf table Number of glyphs that are empty = 3 
P1703 All glyphs in the glyf table are referenced by the loca table

 

## maxp

P1905 Table version is 1.0 and a glyf table is present and no CFF table is present
P1902 Table version is 1.0 and the table is 32 bytes long
P1903 The numGlyphs value equals the number of entries in the loca array plus one numGlyphs = 99 
P1900 The points, contours, and component values match the calculated values

 

## name

P2001 The format selector field is 0
P2007 No strings extended past the end of the table
P2003 The NameRecords array is in sorted order
P2006 No name records are using reserved Name IDs
P2000 The table contains strings for both Mac and Microsoft platforms
P2009 The version string is in the correct format Version 001.000
P2004 All strings had valid Platform Specific Encoding IDs
P2002 All Microsoft unicode strings had valid Language IDs
P2008 The length of every unicode string is an even # of bytes
P2005 The PostScript strings are correctly formatted
P2010 The subfamily string is consistent with the style of the font

 

## post

P2304 The table length is valid
P2308 The version number is valid
P2302 The italicAngle value is reasonable and consistent with other tables
P2305 The underlinePosition value is not less than hhea.Descender
P2306 The underlineThickness value is reasonable
P2301 The isFixedPitch field is consistent with other table(s) matches the hmtx and OS/2 tables 
P2307 The numberOfGlyphs field equals maxp.numGlyphs
P2300 The glyphNameIndex array contains valid indexes
P2303 The names in the post table are consistent with the Adobe Glyph List names

 

## Rasterization Test

P6000 No problems were found during rasterization testing

 


Note: The Font Validator's helpfile contains detailed information about each error message. The latest OpenType specification is available at the Microsoft Typography website. 


```
