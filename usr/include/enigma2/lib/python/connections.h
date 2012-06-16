#ifndef __lib_python_connections_h
#define __lib_python_connections_h

#include <lib/base/sigc.h>
#include <lib/python/python.h>
#include <lib/service/iservice.h>

#include <list>
#include <map>
#include <set>
#include <string>
#include <vector>

#if defined(HAVE_QT)
#include <QByteArray>
#include <QList>
#include <QMap>
#include <QSet>
#include <QString>
#include <QVector>
#endif

class PSignal
{
#ifndef SWIG
protected:
	ePyObject m_list;
public:
	PSignal();
	~PSignal();
	void callPython(SWIG_PYOBJECT(ePyObject) tuple);
	PyObject *getSteal(bool clear=false);
#endif
public:
	PyObject *get();
};

inline void PyDict_SetItem_DECREF(PyObject *p, PyObject *key, PyObject *val)
{
	PyDict_SetItem(p, key, val);
	Org_Py_DECREF(key);
	Org_Py_DECREF(val);
}

inline void PySet_Add_DECREF(PyObject *set, PyObject *key)
{
	PySet_Add(set, key);
	Org_Py_DECREF(key);
}

class PyConv
{
public:
	static inline PyObject *PyFrom(PyObject *src)
	{
		return src;
	}

	static inline PyObject *PyFrom(const void *src)
	{
		return PyLong_FromLong((long)src);
	}

	static inline PyObject *PyFrom(int src)
	{
		return PyLong_FromLong(src);
	}

	static inline PyObject *PyFrom(long src)
	{
		return PyLong_FromLong(src);
	}

	static inline PyObject *PyFrom(long long src)
	{
		return PyLong_FromLongLong(src);
	}

	static inline PyObject *PyFrom(const char *src)
	{
		return PyString_FromString(src);
	}

	/*
	 * convert std::string to a python string
	 */
	static inline PyObject *PyFrom(const std::string &src)
	{
		return PyString_FromStringAndSize(src.data(), src.size());
	}

	/*
	 * convert std::list to a python list
	 */
	template <class T>
	static inline PyObject *PyFrom(const std::list<T> &src)
	{
		PyObject *obj = PyList_New(src.size());

		if (obj) {
			typename std::list<T>::const_iterator i;
			size_t n = 0;
			for (i = src.begin(); i != src.end(); ++i)
				PyList_SET_ITEM(obj, n++, PyFrom(*i));
		}

		return obj;
	}

	/*
	 * convert std::vector to a python list
	 */
	template <class T>
	static inline PyObject *PyFrom(const std::vector<T> &src)
	{
		PyObject *obj = PyList_New(src.size());

		if (obj) {
			typename std::vector<T>::const_iterator i;
			size_t n = 0;
			for (i = src.begin(); i != src.end(); ++i)
				PyList_SET_ITEM(obj, n++, PyFrom(*i));
		}

		return obj;
	}

	/*
	 * convert std::map to a python dict
	 */
	template <class Key, class T>
	static inline PyObject *PyFrom(const std::map<Key, T> &src)
	{
		PyObject *obj = PyDict_New();

		if (obj) {
			typename std::map<Key, T>::const_iterator i;
			for (i = src.begin(); i != src.end(); ++i)
				PyDict_SetItem_DECREF(obj, PyFrom(i->first), PyFrom(i->second));
		}

		return obj;
	}

	/*
	 * convert std::set to a python set
	 */
	template <class Key>
	static inline PyObject *PyFrom(const std::set<Key> &src)
	{
		PyObject *obj = PySet_New(NULL);

		if (obj) {
			typename std::set<Key>::const_iterator i;
			for (i = src.begin(); i != src.end(); ++i)
				PySet_Add_DECREF(obj, PyFrom(*i));
		}

		return obj;
	}

#if defined(HAVE_QT)
	static inline PyObject *PyFrom(const QByteArray &src)
	{
		return PyString_FromStringAndSize(src.constData(), src.size());
	}

	static inline PyObject *PyFrom(const QString &src)
	{
		return PyFrom(src.toUtf8());
	}

	template <class T>
	static inline PyObject *PyFrom(const QList<T> &src)
	{
		PyObject *obj = PyList_New(src.size());

		if (obj) {
			size_t n = 0;
			foreach (const T &e, src)
				PyList_SET_ITEM(obj, n++, PyFrom(e));
		}

		return obj;
	}

	template <class T>
	static inline PyObject *PyFrom(const QVector<T> &src)
	{
		PyObject *obj = PyList_New(src.size());

		if (obj) {
			size_t n = 0;
			foreach (const T &e, src)
				PyList_SET_ITEM(obj, n++, PyFrom(e));
		}

		return obj;
	}

	template <class Key, class T>
	static inline PyObject *PyFrom(const QMap<Key, T> &src)
	{
		PyObject *obj = PyDict_New();

		if (obj) {
			typename QMap<Key, T>::const_iterator i;
			for (i = src.begin(); i != src.end(); ++i)
				PyDict_SetItem_DECREF(obj, PyFrom(i.key()), PyFrom(i.value()));
		}

		return obj;
	}

	template <class Key>
	static inline PyObject *PyFrom(const QSet<Key> &src)
	{
		PyObject *obj = PySet_New(NULL);

		if (obj) {
			foreach (const Key &e, src)
				PySet_Add_DECREF(obj, PyFrom(e));
		}

		return obj;
	}
#endif

	static inline PyObject *PyFrom(ePtr<iRecordableService> &src)
	{
		return New_iRecordableServicePtr(src);
	}
};

template <class R>
class PSignal0: public PSignal, public sigc::signal0<R>
{
public:
	R operator()()
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(0);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal0<R>::operator()();
	}
};

template <class R, class V0>
class PSignal1: public PSignal, public sigc::signal1<R,V0>
{
public:
	R operator()(V0 a0)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(1);
			PyTuple_SET_ITEM(pArgs, 0, PyConv::PyFrom(a0));
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal1<R,V0>::operator()(a0);
	}
};

template <class R, class V0, class V1>
class PSignal2: public PSignal, public sigc::signal2<R,V0,V1>
{
public:
	R operator()(V0 a0, V1 a1)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(2);
			PyTuple_SET_ITEM(pArgs, 0, PyConv::PyFrom(a0));
			PyTuple_SET_ITEM(pArgs, 1, PyConv::PyFrom(a1));
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal2<R,V0,V1>::operator()(a0, a1);
	}
};

template <class R, class V0, class V1, class V2>
class PSignal3: public PSignal, public sigc::signal3<R,V0,V1,V2>
{
public:
	R operator()(V0 a0, V1 a1, V2 a2)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(3);
			PyTuple_SET_ITEM(pArgs, 0, PyConv::PyFrom(a0));
			PyTuple_SET_ITEM(pArgs, 1, PyConv::PyFrom(a1));
			PyTuple_SET_ITEM(pArgs, 2, PyConv::PyFrom(a2));
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal3<R,V0,V1,V2>::operator()(a0, a1, a2);
	}
};

#define PSA_CONSTRUCTOR(...)						\
	PySignalArg(const __VA_ARGS__ &src)				\
	{								\
		m_obj = PyConv::PyFrom(src);				\
	}

#define PSA_CONSTRUCTOR_PTR(...)					\
	PySignalArg(const __VA_ARGS__ *src)				\
	{								\
		m_obj = PyConv::PyFrom(src);				\
	}

class PySignalArg
{
private:
	PyObject *m_obj;

public:
	PySignalArg() : m_obj(0)
	{
	}

	PySignalArg(PyObject *src) : m_obj(src)
	{
	}

	PSA_CONSTRUCTOR(int)
	PSA_CONSTRUCTOR(long)
	PSA_CONSTRUCTOR(long long)
	PSA_CONSTRUCTOR_PTR(void)
	PSA_CONSTRUCTOR_PTR(char)
	PSA_CONSTRUCTOR(std::string)

	template <class T>
	PSA_CONSTRUCTOR(std::list<T>)
	template <class T>
	PSA_CONSTRUCTOR(std::vector<T>)
	template <class Key, class T>
	PSA_CONSTRUCTOR(std::map<Key, T>)
	template <class Key>
	PSA_CONSTRUCTOR(std::set<Key>)

#if defined(HAVE_QT)
	PSA_CONSTRUCTOR(QByteArray)
	PSA_CONSTRUCTOR(QString)

	template <class T>
	PSA_CONSTRUCTOR(QList<T>)
	template <class T>
	PSA_CONSTRUCTOR(QVector<T>)
	template <class Key, class T>
	PSA_CONSTRUCTOR(QMap<Key, T>)
	template <class Key>
	PSA_CONSTRUCTOR(QSet<Key>)
#endif

	operator PyObject *()
	{
		return m_obj;
	}
};

class PySignal0: public PSignal, public sigc::signal0<PySignalArg>
{
public:
	PySignalArg operator()()
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(0);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal0<PySignalArg>::operator()();
	}
};

class PySignal1: public PSignal, public sigc::signal1<PySignalArg, PySignalArg>
{
public:
	PySignalArg operator()(PySignalArg a0)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(1);
			PyTuple_SET_ITEM(pArgs, 0, a0);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal1<PySignalArg, PySignalArg>::operator()(a0);
	}
};

class PySignal2: public PSignal, public sigc::signal2<PySignalArg, PySignalArg, PySignalArg>
{
public:
	PySignalArg operator()(PySignalArg a0, PySignalArg a1)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(2);
			PyTuple_SET_ITEM(pArgs, 0, a0);
			PyTuple_SET_ITEM(pArgs, 1, a1);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal2<PySignalArg, PySignalArg, PySignalArg>::operator()(a0, a1);
	}
};

class PySignal3: public PSignal, public sigc::signal3<PySignalArg, PySignalArg, PySignalArg, PySignalArg>
{
public:
	PySignalArg operator()(PySignalArg a0, PySignalArg a1, PySignalArg a2)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(3);
			PyTuple_SET_ITEM(pArgs, 0, a0);
			PyTuple_SET_ITEM(pArgs, 1, a1);
			PyTuple_SET_ITEM(pArgs, 2, a2);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal3<PySignalArg, PySignalArg, PySignalArg, PySignalArg>::operator()(a0, a1, a2);
	}
};

class PySignal4: public PSignal, public sigc::signal4<PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg>
{
public:
	PySignalArg operator()(PySignalArg a0, PySignalArg a1, PySignalArg a2, PySignalArg a3)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(4);
			PyTuple_SET_ITEM(pArgs, 0, a0);
			PyTuple_SET_ITEM(pArgs, 1, a1);
			PyTuple_SET_ITEM(pArgs, 2, a2);
			PyTuple_SET_ITEM(pArgs, 3, a3);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal4<PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg>::operator()(a0, a1, a2, a3);
	}
};

class PySignal5: public PSignal, public sigc::signal5<PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg>
{
public:
	PySignalArg operator()(PySignalArg a0, PySignalArg a1, PySignalArg a2, PySignalArg a3, PySignalArg a4)
	{
		if (m_list)
		{
			PyObject *pArgs = PyTuple_New(5);
			PyTuple_SET_ITEM(pArgs, 0, a0);
			PyTuple_SET_ITEM(pArgs, 1, a1);
			PyTuple_SET_ITEM(pArgs, 2, a2);
			PyTuple_SET_ITEM(pArgs, 3, a3);
			PyTuple_SET_ITEM(pArgs, 4, a4);
			callPython(pArgs);
			Org_Py_DECREF(pArgs);
		}
		return sigc::signal5<PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg, PySignalArg>::operator()(a0, a1, a2, a3, a4);
	}
};

#endif
