#ifndef __smartptr_h
#define __smartptr_h

#include "object.h"
#include <stdio.h>
#include <string.h>
#include <typeinfo>
#include <lib/base/eerror.h>
#include <lib/python/swig.h>
#include <cxxabi.h>

inline void ptrAssert(void *p, const char *mangled_type)
{
	if (!p) {
		int state;
		char *demangled_type = abi::__cxa_demangle(mangled_type, 0, 0, &state);
		eFatal("dereferenced ePtr<%s> NIL... abort!!", state ? mangled_type : demangled_type);
		if (!state)
			free(demangled_type);
	}
}

template<class T>
class ePtr
{
protected:
	T *ptr;
	char m_ptrStr[sizeof(void*)*2+1];
	void updatePtrStr()
	{
		if (ptr) {
			if (sizeof(void*) > 4)
				sprintf(m_ptrStr, "%llx", (unsigned long long)ptr);
			else
				sprintf(m_ptrStr, "%lx", (unsigned long)ptr);
		}
		else
			strcpy(m_ptrStr, "NIL");
	}
public:
	T &operator*() { return *ptr; }
	ePtr(): ptr(0)
	{
	}
	ePtr(T *c): ptr(c)
	{
		if (c)
			c->AddRef();
		updatePtrStr();
	}
	ePtr(const ePtr &c): ptr(c.ptr)
	{
		if (ptr)
			ptr->AddRef();
		updatePtrStr();
	}
	ePtr &operator=(T *c)
	{
		if (c)
			c->AddRef();
		if (ptr)
			ptr->Release();
		ptr=c;
		updatePtrStr();
		return *this;
	}
	ePtr &operator=(ePtr<T> &c)
	{
		if (c.ptr)
			c.ptr->AddRef();
		if (ptr)
			ptr->Release();
		ptr=c.ptr;
		updatePtrStr();
		return *this;
	}
	~ePtr()
	{
		if (ptr)
			ptr->Release();
	}
	char *getPtrString()
	{
		return m_ptrStr;
	}
#ifndef SWIG
	T* grabRef() { if (!ptr) return 0; ptr->AddRef(); return ptr; }
	T* &ptrref() { ASSERT(!ptr); return ptr; }
	operator bool() const { return !!this->ptr; }
#endif
	T* operator->() const { ptrAssert(ptr, typeid(T).name()); return ptr; }
	operator T*() const { return this->ptr; }
};


template<class T>
class eUsePtr
{
protected:
	T *ptr;
public:
	T &operator*() { return *ptr; }
	eUsePtr(): ptr(0)
	{
	}
	eUsePtr(T *c): ptr(c)
	{
		if (c)
		{
			c->AddRef();
			c->AddUse();
		}
	}
	eUsePtr(const eUsePtr &c)
	{
		ptr=c.ptr;
		if (ptr)
		{
			ptr->AddRef();
			ptr->AddUse();
		}
	}
	eUsePtr &operator=(T *c)
	{
		if (c)
		{
			c->AddRef();
			c->AddUse();
		}
		if (ptr)
		{
			ptr->ReleaseUse();
			ptr->Release();
		}
		ptr=c;
		return *this;
	}
	eUsePtr &operator=(eUsePtr<T> &c)
	{
		if (c.ptr)
		{
			c.ptr->AddRef();
			c.ptr->AddUse();
		}
		if (ptr)
		{
			ptr->ReleaseUse();
			ptr->Release();
		}
		ptr=c.ptr;
		return *this;
	}
	~eUsePtr()
	{
		if (ptr)
		{
			ptr->ReleaseUse();
			ptr->Release();
		}
	}
#ifndef SWIG
	T* grabRef() { if (!ptr) return 0; ptr->AddRef(); ptr->AddUse(); return ptr; }
	T* &ptrref() { ASSERT(!ptr); return ptr; }
#endif
	T* operator->() const { ptrAssert(ptr, typeid(T).name()); return ptr; }
	operator T*() const { return this->ptr; }
};

#endif
