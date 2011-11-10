#ifndef __lib_gui_ecanvas_h
#define __lib_gui_ecanvas_h

#include <lib/gui/epixmap.h>

class eCanvas: public ePixmap
{
	eSize m_clip_size;
	eSize m_canvas_size;
	int m_x1, m_x2, m_y1, m_y2;
protected:
	int event(int event, void* d1=0, void* d2=0);
public:
	eCanvas(eWidget *parent);

	void setSize(eSize size);
	void clear(gRGB color);
	void fillRect(eRect rect, gRGB color);
	void writeText(eRect where, gRGB fg, gRGB bg, gFont *font, const char *string, int flags);
};

#endif
