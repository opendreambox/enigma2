#ifndef __lib_base_signal_h__
#define __lib_base_signal_h__

#ifndef SWIG
#include <sigc++/sigc++.h>
#include <lib/base/eerror.h>
#endif

class eSlot
{
protected:
	sigc::connection conn;
public:
	virtual ~eSlot() { conn.disconnect(); }
};

template <class R>
class eSlot0;

template <class R>
class eSignal0: public sigc::signal<R>
{
public:
	void connect2(eSlot0<R> &slot)
	{
		slot.conn = sigc::signal<R>::connect(slot);
	}
};

template <class R>
class eSlot0: public eSlot
{
	friend class eSignal0<R>;
	operator sigc::slot<R>() { return sigc::mem_fun(*this, &eSlot0<R>::cb_func); }
public:
	virtual R cb_func() { eDebug("default eSlot0::cb_func called!"); return R(); }
};

template <class R, class T>
class eSlot1;

template <class R, class T>
class eSignal1: public sigc::signal<R,T>
{
public:
	void connect2(eSlot1<R,T> &slot)
	{
		slot.conn = sigc::signal1<R,T>::connect(slot);
	}
};

template <class R, class T>
class eSlot1: public eSlot
{
	friend class eSignal1<R,T>;
	operator sigc::slot<R,T>() { return sigc::mem_fun(*this, &eSlot1<R,T>::cb_func); }
public:
	virtual R cb_func(T) { eDebug("default eSlot1::cb_func called!"); return R(); }
};

template <class R, class T, class U>
class eSlot2;

template <class R, class T, class U>
class eSignal2: public sigc::signal<R,T,U>
{
public:
	void connect2(eSlot2<R,T,U> &slot)
	{
		slot.conn = sigc::signal<R,T,U>::connect(slot);
	}
};

template <class R, class T, class U>
class eSlot2: public eSlot
{
	friend class eSignal2<R,T,U>;
	operator sigc::slot<R,T,U>() { return sigc::mem_fun(*this, &eSlot2<R,T,U>::cb_func); }
public:
	virtual R cb_func(T,U) { eDebug("default eSlot2::cb_func called!"); return R(); }
};

template <class R, class T, class U, class V>
class eSlot3;

template <class R, class T, class U, class V>
class eSignal3: public sigc::signal<R,T,U,V>
{
public:
	void connect2(eSlot3<R,T,U,V> &slot)
	{
		slot.conn = sigc::signal<R,T,U,V>::connect(slot);
	}
};

template <class R, class T, class U, class V>
class eSlot3: public eSlot
{
	friend class eSignal3<R,T,U,V>;

	operator sigc::slot<R,T,U,V>() { return sigc::mem_fun(*this, &eSlot3<R,T,U,V>::cb_func); }
public:
	virtual R cb_func(T,U,V) { eDebug("default eSlot3::cb_func called!"); return R(); }
};


template <class R, class T, class U, class V, class W>
class eSlot4;

template <class R, class T, class U, class V, class W>
class eSignal4: public sigc::signal<R,T,U,V,W>
{
public:
	void connect2(eSlot4<R,T,U,V,W> &slot)
	{
		slot.conn = sigc::signal<R,T,U,V,W>::connect(slot);
	}
};

template <class R, class T, class U, class V, class W>
class eSlot4: public eSlot
{
	friend class eSignal4<R,T,U,V,W>;

	operator sigc::slot<R,T,U,V,W>() { return sigc::mem_fun(*this, &eSlot4<R,T,U,V,W>::cb_func); }
public:
	virtual R cb_func(T,U,V,W) { eDebug("default eSlot4::cb_func called!"); return R(); }
};

template <class R, class T, class U, class V, class W, class X>
class eSlot5;

template <class R, class T, class U, class V, class W, class X>
class eSignal5: public sigc::signal<R,T,U,V,W,X>
{
public:
	void connect2(eSlot5<R,T,U,V,W,X> &slot)
	{
		slot.conn = sigc::signal<R,T,U,V,W,X>::connect(slot);
	}
};

template <class R, class T, class U, class V, class W, class X>
class eSlot5: public eSlot
{
	friend class eSignal5<R,T,U,V,W,X>;

	operator sigc::slot<R,T,U,V,W,X>() { return sigc::mem_fun(*this, &eSlot5<R,T,U,V,W,X>::cb_func); }
public:
	virtual R cb_func(T,U,V,W,X) { eDebug("default eSlot5::cb_func called!"); return R(); }
};

#endif /* __lib_base_signal_h__ */
