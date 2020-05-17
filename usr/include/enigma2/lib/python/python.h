#ifndef __lib_python_python_class_h

#ifndef SKIP_PART2
	#define __lib_python_python_class_h
#endif

#include <string>
#include <lib/base/object.h>

#if !defined(SKIP_PART1) && !defined(SWIG)

#if PY_MAJOR_VERSION >= 3
static inline PyObject *ePyBytes_FromStringAndSize(const char *v, Py_ssize_t len)
{
	return PyBytes_FromStringAndSize(v, len);
}

static inline long ePyInt_AS_LONG(PyObject *io)
{
	return PyLong_AsLong(io);
}

static inline long ePyInt_AsLong(PyObject *io)
{
	return PyLong_AsLong(io);
}

static inline unsigned long ePyInt_AsUnsignedLongMask(PyObject *io)
{
	return PyLong_AsUnsignedLong(io);
}

static inline int ePyInt_Check(PyObject *o)
{
	return PyLong_Check(o);
}

static inline PyObject *ePyInt_FromLong(long ival)
{
	return PyLong_FromLong(ival);
}

static inline const char *ePyUnicode_AsUTF8(PyObject *unicode)
{
	return PyUnicode_AsUTF8(unicode);
}

static inline int ePyUnicode_Check(PyObject *o)
{
	return PyUnicode_Check(o);
}

static inline PyObject *ePyUnicode_FromFormatV(const char *format, va_list vargs)
{
	return PyUnicode_FromFormatV(format, vargs);
}

static inline PyObject *ePyUnicode_FromString(const char *u)
{
	return PyUnicode_FromString(u);
}

static inline PyObject *ePyMemoryView_FromMemory(char *mem, Py_ssize_t size, int flags)
{
	return PyMemoryView_FromMemory(mem, size, flags);
}

#else

static inline PyObject *ePyBytes_FromStringAndSize(const char *v, Py_ssize_t len)
{
	return PyString_FromStringAndSize(v, len);
}

static inline long ePyInt_AS_LONG(PyObject *io)
{
	return PyInt_AS_LONG(io);
}

static inline long ePyInt_AsLong(PyObject *io)
{
	return PyInt_AsLong(io);
}

static inline unsigned long ePyInt_AsUnsignedLongMask(PyObject *io)
{
	return PyInt_AsUnsignedLongMask(io);
}

static inline int ePyInt_Check(PyObject *o)
{
	return PyInt_Check(o);
}

static inline PyObject *ePyInt_FromLong(long ival)
{
	return PyInt_FromLong(ival);
}

static inline const char *ePyUnicode_AsUTF8(PyObject *unicode)
{
	return PyString_AS_STRING(unicode);
}

static inline int ePyUnicode_Check(PyObject *o)
{
	return PyString_Check(o);
}

static inline PyObject *ePyUnicode_FromFormatV(const char *format, va_list vargs)
{
	return PyString_FromFormatV(format, vargs);
}

static inline PyObject *ePyUnicode_FromString(const char *u)
{
	return PyString_FromString(u);
}

static inline PyObject *ePyMemoryView_FromMemory(char *mem, Py_ssize_t size, int flags)
{
	if (flags == PyBUF_WRITE)
		return PyBuffer_FromReadWriteMemory(static_cast<void *>(mem), size);
	else
		return PyBuffer_FromMemory(static_cast<void *>(mem), size);
}
#endif

class ePyObject
{
	PyObject *m_ob;
#ifdef PYTHON_REFCOUNT_DEBUG
	const char *m_file;
	int m_line, m_from, m_to;
	bool m_erased;
#endif
public:
	inline ePyObject();
	inline ePyObject(const ePyObject &ob);
	inline ePyObject(PyObject *ob);
#ifdef PYTHON_REFCOUNT_DEBUG
	inline ePyObject(PyObject *ob, const char *file, int line);
#endif
	inline ePyObject(const char *string);
	inline ePyObject(const unsigned char *buf, size_t count);

	operator bool() const { return !!m_ob; }
	operator bool() { return !!m_ob; }
	ePyObject &operator=(const ePyObject &);
	ePyObject &operator=(PyObject *);
	ePyObject &operator=(const char *string);

	operator PyObject*();
	operator PyVarObject*() { return (PyVarObject*)operator PyObject*(); }
	operator PyTupleObject*() { return (PyTupleObject*)operator PyObject*(); }
	operator PyListObject*() { return (PyListObject*)operator PyObject*(); }
#if PY_MAJOR_VERSION >= 3
	operator PyBytesObject*() { return (PyBytesObject*)operator PyObject*(); }
	operator PyUnicodeObject*() { return (PyUnicodeObject*)operator PyObject*(); }
#else
	operator PyStringObject*() { return (PyStringObject*)operator PyObject*(); }
#endif
	operator PyDictObject*() { return (PyDictObject*)operator PyObject*(); }

#ifdef PYTHON_REFCOUNT_DEBUG
	void incref(const char *file, int line);
	void decref(const char *file, int line);
#else
	void incref();
	void decref();
#endif

	ssize_t len() const;
	bool isinstance_str() const;
	const char *str() const;
};

inline ePyObject::ePyObject()
	:m_ob(0)
#ifdef PYTHON_REFCOUNT_DEBUG
	,m_file(0), m_line(0), m_from(0), m_to(0), m_erased(false)
#endif
{
}

inline ePyObject::ePyObject(const ePyObject &ob)
	:m_ob(ob.m_ob)
#ifdef PYTHON_REFCOUNT_DEBUG
	,m_file(ob.m_file), m_line(ob.m_line)
	,m_from(ob.m_from), m_to(ob.m_to), m_erased(ob.m_erased)
#endif
{
}

inline ePyObject::ePyObject(PyObject *ob)
	:m_ob(ob)
#ifdef PYTHON_REFCOUNT_DEBUG
	,m_file(0), m_line(0), m_from(ob?Py_REFCNT(ob):0), m_to(ob?Py_REFCNT(ob):0), m_erased(false)
#endif
{
}

#ifdef PYTHON_REFCOUNT_DEBUG
inline ePyObject::ePyObject(PyObject *ob, const char* file, int line)
	:m_ob(ob)
	,m_file(file), m_line(line), m_from(ob?Py_REFCNT(ob):0), m_to(ob?Py_REFCNT(ob):0), m_erased(false)
{
}
#endif

inline ePyObject::ePyObject(const char *string)
	:m_ob(ePyUnicode_FromString(string))
#ifdef PYTHON_REFCOUNT_DEBUG
	,m_file(0), m_line(0), m_from(ob?Py_REFCNT(ob):0), m_to(ob?Py_REFCNT(ob):0), m_erased(false)
#endif
{
}

inline ePyObject::ePyObject(const unsigned char *buf, size_t count)
	:m_ob(ePyBytes_FromStringAndSize(reinterpret_cast<const char *>(buf), count))
#ifdef PYTHON_REFCOUNT_DEBUG
	,m_file(0), m_line(0), m_from(ob?Py_REFCNT(ob):0), m_to(ob?Py_REFCNT(ob):0), m_erased(false)
#endif
{
}

#ifndef PYTHON_REFCOUNT_DEBUG
inline ePyObject &ePyObject::operator=(PyObject *ob)
{
	m_ob=ob;
	return *this;
}

inline ePyObject &ePyObject::operator=(const ePyObject &ob)
{
	m_ob=ob.m_ob;
	return *this;
}

inline ePyObject &ePyObject::operator=(const char *string)
{
	m_ob = ePyUnicode_FromString(string);
	return *this;
}

inline ePyObject::operator PyObject*()
{
	return m_ob;
}

inline ssize_t ePyObject::len() const
{
	if (m_ob == nullptr)
		return -1;

	return PyObject_Size(m_ob);
}

inline bool ePyObject::isinstance_str() const
{
	return m_ob && ePyUnicode_Check(m_ob);
}

inline const char *ePyObject::str() const
{
	return isinstance_str() ? ePyUnicode_AsUTF8(m_ob) : nullptr;
}

inline void ePyObject::incref()
{
	Py_INCREF(m_ob);
}

inline void ePyObject::decref()
{
	Py_DECREF(m_ob);
}

#endif // ! PYTHON_REFCOUNT_DEBUG

class ePyObjectWrapper
{
	ePyObject m_obj;
public:
	ePyObjectWrapper(const ePyObjectWrapper &wrapper)
		:m_obj(wrapper.m_obj)
	{
		Py_INCREF(m_obj);
	}
	ePyObjectWrapper(const ePyObject &obj)
		:m_obj(obj)
	{
		Py_INCREF(m_obj);
	}
	~ePyObjectWrapper()
	{
		Py_DECREF(m_obj);
	}
	ePyObjectWrapper &operator=(const ePyObjectWrapper &wrapper)
	{
		Py_DECREF(m_obj);
		m_obj = wrapper.m_obj;
		Py_INCREF(m_obj);
		return *this;
	}
	operator PyObject*()
	{
		return m_obj;
	}
	operator ePyObject()
	{
		return m_obj;
	}
};

#endif  // !SWIG && !SKIP_PART1

#ifndef SKIP_PART2
#ifndef SWIG
#ifdef PYTHON_REFCOUNT_DEBUG
inline void Impl_Py_DECREF(const char* file, int line, const ePyObject &obj)
{
	const_cast<ePyObject &>(obj).decref(file, line);
}

inline void Impl_Py_INCREF(const char* file, int line, const ePyObject &obj)
{
	const_cast<ePyObject &>(obj).incref(file, line);
}

inline void Impl_Py_XDECREF(const char* file, int line, const ePyObject &obj)
{
	if (obj)
		const_cast<ePyObject &>(obj).decref(file, line);
}

inline void Impl_Py_XINCREF(const char* file, int line, const ePyObject &obj)
{
	if (obj)
		const_cast<ePyObject &>(obj).incref(file, line);
}

inline ePyObject Impl_PyTuple_New(const char* file, int line, int elements=0)
{
	return ePyObject(PyTuple_New(elements), file, line);
}

inline ePyObject Impl_PyList_New(const char* file, int line, int elements=0)
{
	return ePyObject(PyList_New(elements), file, line);
}

inline ePyObject Impl_PyDict_New(const char* file, int line)
{
	return ePyObject(PyDict_New(), file, line);
}

#if PY_MAJOR_VERSION < 3
inline ePyObject Impl_PyInt_FromLong(const char* file, int line, long val)
{
	return ePyObject(PyInt_FromLong(val), file, line);
}
#endif

inline ePyObject Impl_PyLong_FromLong(const char* file, int line, long val)
{
	return ePyObject(PyLong_FromLong(val), file, line);
}

inline ePyObject Impl_PyLong_FromUnsignedLong(const char* file, int line, unsigned long val)
{
	return ePyObject(PyLong_FromUnsignedLong(val), file, line);
}

inline ePyObject Impl_PyLong_FromUnsignedLongLong(const char* file, int line, unsigned long long val)
{
	return ePyObject(PyLong_FromUnsignedLongLong(val), file, line);
}

inline ePyObject Impl_PyLong_FromLongLong(const char* file, int line, long long val)
{
	return ePyObject(PyLong_FromLongLong(val), file, line);
}

inline ePyObject Impl_PyList_GET_ITEM(const char *file, int line, ePyObject list, unsigned int pos)
{
	return ePyObject(PyList_GET_ITEM(list, pos), file, line);
}

inline ePyObject Impl_PyTuple_GET_ITEM(const char *file, int line, ePyObject list, unsigned int pos)
{
	return ePyObject(PyTuple_GET_ITEM(list, pos), file, line);
}
#else
inline void Impl_Py_DECREF(const ePyObject &obj)
{
	const_cast<ePyObject &>(obj).decref();
}

inline void Impl_Py_INCREF(const ePyObject &obj)
{
	const_cast<ePyObject &>(obj).incref();
}

inline void Impl_Py_XDECREF(const ePyObject &obj)
{
	if (obj)
		const_cast<ePyObject &>(obj).decref();
}

inline void Impl_Py_XINCREF(const ePyObject &obj)
{
	if (obj)
		const_cast<ePyObject &>(obj).incref();
}

inline ePyObject Impl_PyTuple_New(int elements=0)
{
	return PyTuple_New(elements);
}

inline ePyObject Impl_PyList_New(int elements=0)
{
	return PyList_New(elements);
}

inline ePyObject Impl_PyDict_New()
{
	return PyDict_New();
}

#if PY_MAJOR_VERSION < 3
inline ePyObject Impl_PyInt_FromLong(long val)
{
	return PyInt_FromLong(val);
}
#endif

inline ePyObject Impl_PyLong_FromLong(long val)
{
	return PyLong_FromLong(val);
}

inline ePyObject Impl_PyLong_FromUnsignedLong(unsigned long val)
{
	return PyLong_FromUnsignedLong(val);
}

inline ePyObject Impl_PyLong_FromUnsignedLongLong(unsigned long long val)
{
	return PyLong_FromUnsignedLongLong(val);
}

inline ePyObject Impl_PyLong_FromLongLong(long long val)
{
	return PyLong_FromLongLong(val);
}

inline ePyObject Impl_PyList_GET_ITEM(ePyObject list, unsigned int pos)
{
	return PyList_GET_ITEM(list, pos);
}

inline ePyObject Impl_PyTuple_GET_ITEM(ePyObject list, unsigned int pos)
{
	return PyTuple_GET_ITEM(list, pos);
}
#endif

inline void Impl_INCREF(PyObject *ob)
{
	Py_INCREF(ob);
}

inline void Impl_DECREF(PyObject *ob)
{
	Py_DECREF(ob);
}
#define Org_Py_INCREF(obj) Impl_INCREF(obj)
#define Org_Py_DECREF(obj) Impl_DECREF(obj)
#undef Py_DECREF
#undef Py_XDECREF
#undef Py_INCREF
#undef Py_XINCREF
#undef PyList_GET_ITEM
#undef PyTuple_GET_ITEM
#ifdef PYTHON_REFCOUNT_DEBUG
#define Py_DECREF(obj) Impl_Py_DECREF(__FILE__, __LINE__, obj)
#define Py_XDECREF(obj) Impl_Py_XDECREF(__FILE__, __LINE__, obj)
#define Py_INCREF(obj) Impl_Py_INCREF(__FILE__, __LINE__, obj)
#define Py_XINCREF(obj) Impl_Py_XINCREF(__FILE__, __LINE__, obj)
#define PyList_New(args...) Impl_PyList_New(__FILE__, __LINE__, args)
#define PyTuple_New(args...) Impl_PyTuple_New(__FILE__, __LINE__, args)
#define PyDict_New(...) Impl_PyDict_New(__FILE__, __LINE__)
#if PY_MAJOR_VERSION < 3
#define PyInt_FromLong(val) Impl_PyInt_FromLong(__FILE__, __LINE__, val)
#endif
#define PyLong_FromLong(val) Impl_PyLong_FromLong(__FILE__, __LINE__, val)
#define PyLong_FromUnsignedLong(val) Impl_PyLong_FromUnsignedLong(__FILE__, __LINE__, val)
#define PyLong_FromUnsignedLongLong(val) Impl_PyLong_FromUnsignedLongLong(__FILE__, __LINE__, val)
#define PyLong_FromLongLong(val) Impl_PyLong_FromLongLong(__FILE__, __LINE__, val)
#define PyList_GET_ITEM(list, pos) Impl_PyList_GET_ITEM(__FILE__, __LINE__, list, pos)
#define PyTuple_GET_ITEM(list, pos) Impl_PyTuple_GET_ITEM(__FILE__, __LINE__, list, pos)
#else
#define Py_DECREF(obj) Impl_Py_DECREF(obj)
#define Py_XDECREF(obj) Impl_Py_XDECREF(obj)
#define Py_INCREF(obj) Impl_Py_INCREF(obj)
#define Py_XINCREF(obj) Impl_Py_XINCREF(obj)
#define PyList_New(args...) Impl_PyList_New(args)
#define PyTuple_New(args...) Impl_PyTuple_New(args)
#define PyDict_New(...) Impl_PyDict_New()
#if PY_MAJOR_VERSION < 3
#define PyInt_FromLong(val) Impl_PyInt_FromLong(val)
#endif
#define PyLong_FromLong(val) Impl_PyLong_FromLong(val)
#define PyLong_FromUnsignedLong(val) Impl_PyLong_FromUnsignedLong(val)
#define PyLong_FromUnsignedLongLong(val) Impl_PyLong_FromUnsignedLongLong(val)
#define PyLong_FromLongLong(val) Impl_PyLong_FromLongLong(val)
#define PyList_GET_ITEM(list, pos) Impl_PyList_GET_ITEM(list, pos)
#define PyTuple_GET_ITEM(list, pos) Impl_PyTuple_GET_ITEM(list, pos)
#endif

class ePython
{
public:
	ePython();
	~ePython();
	int execFile(const char *file);
	int execute(const std::string &pythonfile, const std::string &funcname);
	static int call(ePyObject pFunc, ePyObject args);
	static ePyObject resolve(const std::string &pythonfile, const std::string &funcname);
	static void dumpStackTrace();
private:
};

#define ePyInt_AsLongSafe(ob) __extension__ \
({ \
	long ret = ePyInt_AsLong(ob); \
	if (PyErr_Occurred()) \
	{ \
		PyErr_Print(); \
		ePython::dumpStackTrace(); \
		ASSERT(0); \
	} \
	ret; \
} )

#define ePyInt_AsUnsignedLongMaskSafe(ob) __extension__ \
({ \
	unsigned long ret = ePyInt_AsUnsignedLongMask(ob); \
	if (PyErr_Occurred()) \
	{ \
		PyErr_Print(); \
		ePython::dumpStackTrace(); \
		ASSERT(0); \
	} \
	ret; \
} )

#define PyLong_AsLongSafe(ob) __extension__ \
({ \
	long ret = PyLong_AsLong(ob); \
	if (PyErr_Occurred()) \
	{ \
		PyErr_Print(); \
		ePython::dumpStackTrace(); \
		ASSERT(0); \
	} \
	ret; \
} )

#define PyLong_AsLongLongSafe(ob) __extension__ \
({ \
	long long ret = PyLong_AsLongLong(ob); \
	if (PyErr_Occurred()) \
	{ \
		PyErr_Print(); \
		ePython::dumpStackTrace(); \
		ASSERT(0); \
	} \
	ret; \
} )

#define ePyUnicode_AsUTF8Safe(ob) __extension__ \
({ \
	if (!ePyUnicode_Check(ob)) \
	{ \
		ePython::dumpStackTrace(); \
		ASSERT(0); \
	} \
	ePyUnicode_AsUTF8(ob); \
} )

#if PY_MAJOR_VERSION >= 3
  #define PYMOD_SUCCESS_VAL(val) val
  #define PYMOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
  #define PYMOD_DEF(name, doc, methods) ({ \
          static struct PyModuleDef moduledef = { \
            PyModuleDef_HEAD_INIT, name, doc, -1, methods, }; \
          PyModule_Create(&moduledef); \
  })
#else
  static inline void PYMOD_SUCCESS_VAL(PyObject *m) {}
  #define PYMOD_INIT(name) void init##name(void)
  #define PYMOD_DEF(name, doc, methods) \
          Py_InitModule3(name, methods, doc);
#endif

#if PY_MAJOR_VERSION < 3
extern int _Py_Finalizing;
#endif

#if PY_VERSION_HEX < 0x03070000
static inline int _Py_IsFinalizing(void)
{
	return _Py_Finalizing;
}
#endif

#endif // SWIG
#endif // SKIP_PART2
#endif // __lib_python_python_class_h
