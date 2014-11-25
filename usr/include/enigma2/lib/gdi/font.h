#ifndef __FONT_H
#define __FONT_H

#ifndef SWIG

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_CACHE_H
#include FT_CACHE_IMAGE_H
#include FT_CACHE_SMALL_BITMAPS_H
typedef FTC_ImageCache FTC_Image_Cache;
typedef FTC_ImageTypeRec FTC_Image_Desc;
typedef FTC_SBitCache FTC_SBit_Cache;
#include <vector>
#include <list>

#include <lib/gdi/esize.h>
#include <lib/gdi/epoint.h>
#include <lib/gdi/erect.h>
#include <string>
#include <lib/base/object.h> 

#include <set>

class FontRenderClass;
class eFont;
class gDC;
class gFont;
class gRegion;
class gRGBA;
class gSurface;

#endif
class fontRenderClass
{ 
#ifndef SWIG
	friend class eFont;
	friend class eTextPara;
	friend class gFont;

protected:
	struct fontListEntry
	{
		std::string filename, face;
		int scale; // 100 is 1:1
		long id;
		fontListEntry *next;
		~fontListEntry();
	} *font;

	fontListEntry *findFace(const std::string &face);
	fontListEntry *findId(FTC_FaceID id);

private:
	FT_Library library;
	FTC_Manager			cacheManager;				/* the cache manager							 */
	FTC_Image_Cache	imageCache;					/* the glyph image cache					 */
	FTC_SBit_Cache	 sbitsCache;				/* the glyph small bitmaps cache	 */

	FT_Error getGlyphBitmap(FTC_Image_Desc *font, FT_ULong glyph_index, FTC_SBit *sbit);
	static fontRenderClass *instance;
#else
	fontRenderClass();
	~fontRenderClass();
#endif
public:
	float getLineHeight(const gFont& font);
	static fontRenderClass *getInstance();
#ifndef SWIG
	std::string AddFont(const std::string &filename, const std::string &name, int scale);
	FT_Error FTC_Face_Requester(FTC_FaceID	face_id, FT_Face* aface);
	long getFaceID(const std::string &face);
	int getFont(ePtr<eFont> &font, const std::string &face, int size, int tabwidth=-1);
	fontRenderClass();
	~fontRenderClass();
#endif
};

#ifndef SWIG

#define RS_WRAP		1
#define RS_DOT		2
#define RS_DIRECT	4
#define RS_FADE		8

#define GS_ISSPACE  1
#define GS_ISFIRST  2
#define GS_USED			4
#define GS_INVERT   8
#define GS_SOFTHYPHEN 16
#define GS_HYPHEN   32
#define GS_CANBREAK (GS_ISSPACE|GS_SOFTHYPHEN|GS_HYPHEN)

class pGlyph
{
public:
#if defined(__GXX_EXPERIMENTAL_CXX0X__)
	/* hmm... not sure why the default operator isn't good enough
	 * to use this class in a std::vector
	 */
	pGlyph &operator=(const pGlyph &p)
	{
		x = p.x;
		y = p.y;
		w = p.w;
		argb = p.argb;
		font = p.font;
		glyph_index = p.glyph_index;
		flags = p.flags;
		bbox = p.bbox;
		return *this;
	}
#endif

	int x, y, w;
	unsigned int argb;
	ePtr<eFont> font;
	FT_ULong glyph_index;
	int flags;
	eRect bbox;
};

typedef std::vector<pGlyph> glyphString;

class eFont;
class eLCD;

class eTextPara: public iObject
{
	DECLARE_REF(eTextPara);
	ePtr<eFont> current_font, replacement_font;
	FT_Face current_face, replacement_face;
	int use_kerning;
	int previous;
	static std::string replacement_facename;
	static std::set<int> forced_replaces;

	eRect area;
	ePoint cursor;
	eSize maximum;
	int left;
	glyphString glyphs;
	std::list<int> lineOffsets;
	std::list<int> lineChars;
	int charCount;
	bool doTopBottomReordering;

	int appendGlyph(eFont *current_font, FT_Face current_face, FT_UInt glyphIndex, int flags, int rflags, unsigned long &argb);
	void newLine(int flags);
	void setFont(eFont *font, eFont *replacement_font);
	eRect boundBox;
	void calc_bbox();
	int bboxValid;
	void clear();
public:
	eTextPara(eRect area, ePoint start=ePoint(-1, -1))
		:current_font(0), replacement_font(0), current_face(0), replacement_face(0)
		,area(area), cursor(start), maximum(0, 0), left(start.x()), charCount(0)
		,doTopBottomReordering(false), bboxValid(0)
	{
	}
	virtual ~eTextPara();
	
	static void setReplacementFont(const std::string &font) { replacement_facename=font; }
	static void forceReplacementGlyph(int unicode) { forced_replaces.insert(unicode); }

	void setFont(const gFont *font);
	int renderString(const char *string, int flags=0);
	void blit(gSurface *surface, const gRegion &clip, const ePoint &offset, const gRGBA &background, const gRGBA &foreground);

	enum
	{
		dirLeft, dirRight, dirCenter, dirBlock
	};

	void realign(int dir);

	const eRect & getBoundBox()
	{
		if (!bboxValid)
			calc_bbox();

		return boundBox;
	}
	
	int size() const
	{
		return glyphs.size();
	}

	const eRect& getGlyphBBox(int num) const
	{
		ASSERT(num >= 0);
		ASSERT(num < (int)glyphs.size());
		return glyphs[num].bbox;
	}
	
	void setGlyphFlag(int g, int f)
	{
		ASSERT(g >= 0);
		ASSERT(g < (int)glyphs.size());
		glyphs[g].flags |= f;
	}

	void clearGlyphFlag(int g, int f)
	{
		ASSERT(g >= 0);
		ASSERT(g < (int)glyphs.size());
		glyphs[g].flags |= f;
	}
};

class eFont: public iObject
{
	DECLARE_REF(eFont);
public:
	FTC_ScalerRec scaler;
	FTC_Image_Desc font;
	fontRenderClass *renderer;
	FT_Error getGlyphBitmap(FT_ULong glyph_index, FTC_SBit *sbit);
	FT_Face face;
	FT_Size size;
	
	int tabwidth;
	int height;
	eFont(fontRenderClass *render, FTC_FaceID faceid, int isize, int tabwidth);
	virtual ~eFont();
};

extern fontRenderClass *font;

#endif  // !SWIG

#endif
