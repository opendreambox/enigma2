#ifndef __lib_listbox_h
#define __lib_listbox_h

#include <lib/gui/ewidget.h>
#include <lib/base/connection.h>

class eListbox;
class eSlider;
class gPixmap;

class iListboxContent: public iObject
{
public:
	virtual ~iListboxContent()=0;
	
		/* indices go from 0 to size().
		   the end is reached when the cursor is on size(), 
		   i.e. one after the last entry (this mimics 
		   stl behavior)
		   
		   cursors never invalidate - they can become invalid
		   when stuff is removed. Cursors will always try
		   to stay on the same data, however when the current
		   item is removed, this won't work. you'll be notified
		   anyway. */
#ifndef SWIG	
protected:
	iListboxContent();
	friend class eListbox;
	virtual void updateClip(gRegion &){ };
	virtual void cursorHome()=0;
	virtual void cursorEnd()=0;
	virtual int cursorMove(int count=1)=0;
	virtual int cursorValid()=0;
	virtual int cursorSet(int n)=0;
	virtual int cursorGet()=0;
	
	virtual void cursorSave()=0;
	virtual void cursorRestore()=0;
	
	virtual int size()=0;
	
	virtual int currentCursorSelectable();
	
	void setListbox(eListbox *lb);
	
	// void setOutputDevice ? (for allocating colors, ...) .. requires some work, though
	virtual void setSize(const eSize &size)=0;
	
		/* the following functions always refer to the selected item */
	virtual void paint(gPainter &painter, eWindowStyle &style, const ePoint &offset, int selected)=0;
	
	virtual int getItemHeight()=0;
	virtual int getItemWidth() { return -1; }
	
	eListbox *m_listbox;
#endif
};

#ifndef SWIG
struct eListboxStyle
{
	ePtr<gPixmap> m_background, m_selection;
	int m_transparent_background;
	gRGB m_background_color, m_background_color_selected, m_foreground_color, m_foreground_color_selected;
	int m_background_color_set, m_foreground_color_set, m_background_color_selected_set, m_foreground_color_selected_set;

		/*
			{m_transparent_background m_background_color_set m_background}
			{0 0 0} use global background color
			{0 1 x} use background color
			{0 0 p} use background picture
			{1 x 0} use transparent background
			{1 x p} use transparent background picture
		*/
};
#endif

class eListbox: public eWidget
{
	SWIG_AUTODOC
	E_DECLARE_PRIVATE(eListbox)
	void updateScrollBar();
	static bool wrap_around_default;
public:
	eListbox(eWidget *parent, bool withActionMap=true);
	~eListbox();

	static void setWrapAroundDefault(bool on);

	eSignal0<void> selectionChanged;

	enum {
		layoutVertical,
		layoutHorizontal,
		layoutGrid,
	};

	enum {
		showOnDemand,
		showAlways,
		showNever
	};

	void setScrollbarMode(int mode);
	void setupScrollbar();
	void setWrapAround(bool);
	void setBacklogMode(bool);

	void setContent(iListboxContent *content);

/*	enum Movement {
		moveUp,
		moveDown,
		moveTop,
		moveEnd,
		justCheck
	}; */

	int getCurrentIndex();
	void moveSelection(long how);
	void moveSelectionTo(int index);
	void moveToEnd();
	bool atBegin();
	bool atEnd();

	enum ListboxActions {
		moveUp,
		moveDown,
		moveTop,
		moveEnd,
		pageUp,
		pageDown,
		justCheck,
		refresh,
		moveLeft,
		moveRight
	};

	void setMode(int mode);
	void setItemHeight(int h);
	void setItemWidth(int w);
	void setMargin(const ePoint &margin);
	void setSelectionZoom(float zoom);
	void setSelectionEnable(int en);

	void setBackgroundColor(gRGB &col);
	void setBackgroundColorSelected(gRGB &col);
	void setForegroundColor(gRGB &col);
	void setForegroundColorSelected(gRGB &col);
	void setBackgroundPicture(ePtr<gPixmap> &pixmap);
	void setSelectionPicture(ePtr<gPixmap> &pixmap);

	void setScrollbarSliderPicture(ePtr<gPixmap> &pm);
	void setScrollbarSliderBackgroundPicture(ePtr<gPixmap> &pm);
	void setScrollbarValuePicture(ePtr<gPixmap> &pm);
	void setScrollbarSliderBorderWidth(int size);
	void setScrollbarWidth(int size);

	void setScrollbarBackgroundPixmapTopHeight(int value);
	void setScrollbarBackgroundPixmapBottomHeight(int value);
	void setScrollbarValuePixmapTopHeight(int value);
	void setScrollbarValuePixmapBottomHeight(int value);

	void resetScrollbarProperties();

	int getEntryTop();
	int getVisibleItemCount();
	const eRect getSelectionRect(bool zoomed=false);
#ifndef SWIG
	struct eListboxStyle *getLocalStyle(void);

		/* entryAdded: an entry was added *before* the given index. it's index is the given number. */
	void entryAdded(int index);
		/* entryRemoved: an entry with the given index was removed. */
	void entryRemoved(int index);
		/* entryChanged: the entry with the given index was changed and should be redrawn. */
	void entryChanged(int index);
		/* the complete list changed. you should not attemp to keep the current index. */
	void entryReset(bool cursorHome=true);

	void invalidate(const gRegion &region = gRegion::invalidRegion());

	int itemHeight();
	int itemWidth();

protected:
	int event(int event, void *data=0, void *data2=0);
	void recalcSize();

	const ePoint calculatePosition(int at);
	const ePoint calculatePositionInGrid(int at);
	const eRect entryRect(int position);
	const eRect selectionRect(int position);

	void hapticFeedback();
#endif
};

#endif
