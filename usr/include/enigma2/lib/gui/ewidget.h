#ifndef __lib_gui_ewidget_h
#define __lib_gui_ewidget_h

#include <lib/gdi/grc.h> /* for gRegion */
#include <lib/base/object.h>
#include <lib/base/eptrlist.h> /* for eSmartPtrList */
#include <lib/gui/ewindowstyle.h> /* for eWindowStyle */

class eWidgetDesktop;
class eWidgetAnimationSet;
class eWidgetDesktopCompBuffer;
class eLabel;

class eWidget : public iSyncPaintable
{
	SWIG_AUTODOC
	friend class eWidgetDesktop;
	friend class eLabel;
	friend class eWidgetAnimationSet;
public:
	eWidget(eWidget *parent);
	virtual ~eWidget();

	void move(ePoint pos);
	void resize(eSize size);

	ePoint position() const { return m_position; }
	eSize size() const { return m_size; }
	eSize csize() const { return m_client_size; }
	eWidget *parent() const;
	eSize parentSize() const;
	eSize parentCsize() const;

	void invalidate(const gRegion &region = gRegion::invalidRegion());
	virtual void invalidateForAnimation();

		/* the window were to attach childs to. Normally, this
		   is "this", but it can be overridden in case a widget
		   has a "client area", which is implemented as a child
		   widget. eWindow overrides this, for example. */
	virtual eWidget *child() { return this; }

	void show();
	void hide();
	void doHide();

	void destruct();

	SWIG_VOID(int) getStyle(ePtr<eWindowStyle> &SWIG_NAMED_OUTPUT(style)) { if (!m_style) return 1; style = m_style; return 0; }
	void setStyle(eWindowStyle *style) { m_style = style; }

	void setBackgroundColor(const gRGB &col);
	void clearBackgroundColor();

	void setZPosition(int z);
	void setTransparent(int transp);

	int isVisible() { return (m_vis & wVisShow) && (!m_parent || m_parent->isVisible()); }
	const bool isFading() const;

	void disable();
	void enable();
	bool isEnabled(){ return m_enabled; };

	void onAnimationFinished();
	void signalHideAnimationFinished();
	virtual bool canAnimate(){ return false; };
	virtual bool isFinishedAnimating() const;

	//merely for debugging purposes
	void setParentTitle(const std::string &title){ m_parent_title = title; }

	bool setShowHideAnimation(const std::string &key);
	void setPulsate(bool enabled, int64_t duration=1000, float from=0.3, float to=1.0);

	virtual int isTransparent() { return m_vis & wVisTransparent; }

	ePoint getAbsolutePosition();

	eSignal0<void> hideAnimationFinished;
	eSignal0<void> showAnimationFinished;

protected:
	eWidgetDesktop *m_desktop;

	int m_vis;

	ePoint m_position;
	eSize m_size, m_client_size;
		/* will be accounted when there's a client offset */
	eSize m_client_offset;
	eWidget *m_parent;

	void insertIntoParent();
	void doPaint(gPainter *painter, const gRegion &region);
	void recalcClipRegionsWhenVisible();

	void parentRemoved();

	gRGB m_background_color;
	int m_have_background_color;

	eWidget *m_current_focus, *m_focus_owner;

	int m_notify_child_on_position_change;

	ePtr<eTimer> m_haftimer;

	void mayKillFocus();

	enum {
		wVisShow = 1,
		wVisTransparent = 2,
		wVisFade = 4,
	};

	ePtrList<eWidget> m_childs;
	bool m_enabled;

	int m_z_position;
	ePtr<eWindowStyle> m_style;
	eWidgetDesktopCompBuffer *m_comp_buffer;
	ePtr<eWidgetAnimationSet> m_animations;
	bool m_animations_enabled;
	bool m_can_animate;
	bool m_uses_default_animations;
	ePtr<eTimer> m_invalidationTimer;
	std::string m_parent_title;

	virtual eWidgetDesktop *desktop(eWidget **root=NULL, bool die=false) const;
	gPixelFormat pixelFormat() const;

public:

		// all in local space!
	gRegion	m_clip_region, m_visible_region, m_visible_with_childs;

	enum eWidgetEvent
	{
		evtPaint,
		evtPrefetch,
		evtKey,
		evtChangedPosition,
		evtChangedSize,

		evtParentChangedPosition,

		evtParentVisibilityChanged,
		evtWillChangePosition, /* new size is eRect *data */
		evtWillChangeSize,

		evtAction,

		evtFocusGot,
		evtFocusLost,

		evtUserWidget,
	};
	virtual int event(int event, void *data = 0, void *data2 = 0);
	void setFocus(eWidget *focus);

		/* enable this if you need the absolute position of the widget */
	void setPositionNotifyChild(int n) { m_notify_child_on_position_change = n; }

	void notifyShowHide();
};

extern eWidgetDesktop *getDesktop(int which);

#endif
