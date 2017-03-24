#ifndef __grc_h
#define __grc_h

/*
	gPainter ist die high-level version. die highlevel daten werden zu low level opcodes ueber
	die gRC-queue geschickt und landen beim gDC der hardwarespezifisch ist, meist aber auf einen
	gPixmap aufsetzt (und damit unbeschleunigt ist).
*/

#if defined(Q_MOC_RUN)
#include "enigma2_config.h"
#endif

#include <pthread.h>
#include <stack>
#include <list>

#include <string>
#include <lib/base/elock.h>
#include <lib/base/message.h>
#include <lib/base/thread.h>
#include <lib/gdi/color.h>
#include <lib/gdi/erect.h>
#include <lib/gdi/gpixmap.h>
#include <lib/gdi/matrix.h>
#include <lib/gdi/region.h>
#include <lib/gdi/gfont.h>

class eTextPara;
class gPalette;

class gDC;
class iSyncPaintable;
class gOpcode
{
public:
	enum Opcode
	{
		renderPara,
		
		fill, fillRegion, fillRects, clear,
		blit,

		setPalette,
		mergePalette,
		
		line,
		
		setBackgroundColor,
		setForegroundColor,
		
		setBackgroundColorRGB,
		setForegroundColorRGB,
		
		setOffset,
		
		setClip, addClip, popClip,
		
		flush,
		
		swapBuffers,
		notify,
		
		enableSpinner, disableSpinner, incrementSpinner,
		
		shutdown,

		setMatrix,

		syncPaint,
	} opcode;

	gDC *dc;

	union para
	{
		struct pfillRect
		{
			eRect area;
			int flags;
		} *fill;

		struct pfillRegion
		{
			gRegion region;
			int flags;
		} *fillRegion;

		struct pfillRects
		{
			std::vector<eRect> rects;
			eRect bbox;
			int flags;
		} *fillRects;

		struct prenderPara
		{
			ePoint offset;
			eTextPara *textpara;
		} *renderPara;

		struct psetPalette
		{
			gPalette *palette;
		} *setPalette;

		struct pblit
		{
			ePtr<gPixmap> pixmap;
			int flags;
			eRect position;
			eRect clip;
			float alpha;
		} *blit;

		struct pmergePalette
		{
			ePtr<gPixmap> target;
		} *mergePalette;

		struct pline
		{
			ePoint start, end;
			int flags;
		} *line;

		struct psetClip
		{
			gRegion region;
		} *clip;

		struct psetColor
		{
			gColor color;
		} *setColor;

		struct psetColorRGB
		{
			gRGBA color;
		} *setColorRGB;

		struct psetOffset
		{
			ePoint value;
			int rel;
		} *setOffset;

		struct pvideoMode
		{
			eSize resolution;
			unsigned int bpp;
		} *videoMode;

		struct psetMatrix
		{
			eMatrix4x4 matrix;
		} *setMatrix;

		struct psyncPaint
		{
			iSyncPaintable *target;
		} *syncPaint;

		para()
			:fill(NULL)
		{
		}
	} parm;

	gOpcode(enum Opcode o = shutdown);
	gOpcode(enum Opcode o, ePtr<gDC> &dc);
	std::string toString() const;
private:
	std::string parmString() const;
};

#define MAXSIZE 2048

		/* gRC is the singleton which controls the fifo and dispatches commands */
class gRC : public eThread, public iObject, public sigc::trackable
{
	DECLARE_REF(gRC);
	friend class gPainter;
	friend class gFBDC;
	friend class gMainDC;
	friend class gQtDC;
	static gRC *instance;

	pthread_mutex_t mutex;
	pthread_cond_t cond;
	bool m_locked;
	virtual void thread();

	gOpcode queue[MAXSIZE];
	int rp, wp;

	eFixedMessagePump<int> m_notify_pump;
	void recv_notify(const int &i);

	ePtr<gDC> m_spinner_dc;
	int m_spinner_enabled;
	
	void enableSpinner();
	void disableSpinner();
	
	int m_prev_idle_count;

	void lock();
	void unlock();

public:
	gRC();
	virtual ~gRC();

	void submit(const gOpcode &o);

	sigc::signal0<void> notify;
	
	void setSpinnerDC(gDC *dc) { m_spinner_dc = dc; }
	
	static gRC *getInstance();
};

	/* gPainter is the user frontend, which in turn sends commands through gRC */
class gPainter
{
	friend class gRC;

protected:
	ePtr<gDC> m_dc;
	ePtr<gFont> m_font;

	void begin(const eRect &rect);
	void end();

	virtual void submit(const gOpcode::Opcode o, const gOpcode::para &parm = gOpcode::para());

public:
	gPainter(gDC *dc);
	virtual ~gPainter();

	void setBackgroundColor(const gColor &color);
	void setForegroundColor(const gColor &color);

	void setBackgroundColor(const gRGBA &color);
	void setForegroundColor(const gRGBA &color);

	void setFont(gFont *font);
		/* flags only THESE: */
	enum
	{
			// todo, make mask. you cannot align both right AND center AND block ;)
		RT_HALIGN_LEFT = 0,  /* default */
		RT_HALIGN_RIGHT = 1,
		RT_HALIGN_CENTER = 2,
		RT_HALIGN_BLOCK = 4,
		
		RT_VALIGN_TOP = 0,  /* default */
		RT_VALIGN_CENTER = 8,
		RT_VALIGN_BOTTOM = 16,
		
		RT_WRAP = 32,
		RT_FILLED_BOX = 64
	};
	void renderText(const eRect &position, const std::string &string, int flags=0);
	
	void renderPara(eTextPara *para, const ePoint &offset = ePoint(0, 0));

	void fill(const eRect &area, int flags = 0);
	void fill(const gRegion &area, int flags = 0);
	void fill(const std::vector<eRect> &rects, const eRect &bbox = eRect::invalidRect(), int flags = 0);
	
	void clear();

	enum
	{
		BT_ALPHATEST = gPixmap::blitAlphaTest,
		BT_ALPHABLEND = gPixmap::blitAlphaBlend,
		BT_SCALE = gPixmap::blitScale, /* will be automatically set by blitScale */
		BT_DESTINATION_COLOR_PLUS_ZERO = gPixmap::blitDestinationColorPlusZero,
		BT_ONE_PLUS_ONE = gPixmap::blitOnePlusOne,
		BT_SOURCEALPHA_PLUS_ONE = gPixmap::blitSourceAlphaPlusOne,
	};

	void blit(const ePtr<gPixmap> &pixmap, const ePoint &pos, const eRect &clip=eRect(), int flags=0, float alpha = 1.0);
	void blitScale(const ePtr<gPixmap> &pixmap, const eRect &pos, const eRect &clip=eRect(), int flags=0, float alpha = 1.0);

	void setPalette(const gRGBA *colors, unsigned int len=256);
	void setPalette(const ePtr<gPixmap> &source);
	void mergePalette(const ePtr<gPixmap> &target);
	
	void line(const ePoint &start, const ePoint &end, int flags = 0);

	void setOffset(const ePoint &abs);
	void moveOffset(const ePoint &rel);
	void resetOffset();
	
	void resetClip(const gRegion &clip);
	void clip(const gRegion &clip);
	void clippop();

	void swapBuffers();
	void notify();
	
	void flush();
	virtual void sync();

	void requestSyncPaint(iSyncPaintable *target);

	void setMatrix(const eMatrix4x4 &matrix);
	int flags();
};

class gSyncPainter : public gPainter
{
protected:
	virtual void submit(const gOpcode::Opcode o, const gOpcode::para &parm = gOpcode::para());
	virtual void sync();

public:
	gSyncPainter(gDC *dc);
	virtual ~gSyncPainter();
};

class gDC: public iObject
{
	DECLARE_REF(gDC);

	gRegion m_dirtyRegion;

protected:
	ePtr<gPixmap> m_pixmap;

	gColor m_foreground_color, m_background_color;
	gRGBA m_foreground_color_rgb, m_background_color_rgb;
	ePoint m_current_offset;
	
	std::stack<gRegion> m_clip_stack;
	gRegion m_current_clip;

	eMatrix4x4 m_matrix;
	
	ePtr<gPixmap> m_spinner_saved;
	ePtr<gPixmap> *m_spinner_pic;
	eRect m_spinner_pos;
	int m_spinner_num, m_spinner_i;

	const gRegion &dirtyRegion() const { return m_dirtyRegion; }
	void invalidate(const gRegion &region = gRegion::invalidRegion());

	virtual gSurface *surface() const { return m_pixmap ? m_pixmap->surface() : 0; }

public:
	virtual void exec(const gOpcode *opcode);
	gDC(ePtr<gPixmap> pixmap);
	gDC();
	virtual ~gDC();
	gRegion &getClip() { return m_current_clip; }
	int getPixmap(ePtr<gPixmap> &pm) { pm = m_pixmap; return 0; }
	gRGBA getRGB(gColor col);
	int flags(){ return m_pixmap ? m_pixmap->flags() : 0; }
	virtual eSize size() { return m_pixmap ? m_pixmap->size() : eSize(0, 0); }
	virtual gPixelFormat pixelFormat() const;
	virtual int islocked() { return 0; }
	
	virtual void enableSpinner();
	virtual void disableSpinner();
	virtual void incrementSpinner();
	virtual void setSpinner(eRect pos, ePtr<gPixmap> *pic, int len);
};

class iSyncPaintable
{
	friend class gDC;
protected:
	virtual void doSyncPaint(gSyncPainter *painter) {};
};

#endif
