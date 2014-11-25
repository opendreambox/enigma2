#ifndef __lib_python_swig_h
#define __lib_python_swig_h

#ifdef SWIG
#define SWIG_IGNORE(x) %ignore x
#define SWIG_AUTODOC %feature("autodoc", "1");
#ifdef SWIGPYTHON_BUILTIN
    #define SWIG_HASH_FUNC(class,func) %feature("python:slot", "tp_hash", functype="hashfunc") class::func
    #define SWIG_IGNORE_ENUMS(x) %ignore x; %pythoncode %{x = _enigma.x##_ENUMS%}
#else
    #define SWIG_HASH_FUNC(class,func) %pythoncode %{class.__hash__ = class.func%}
    #define SWIG_IGNORE_ENUMS(x) %ignore x; %pythoncode %{x = x##_ENUMS%}
#endif
#define SWIG_EXTEND(x, code) %extend x { code }
#define SWIG_TEMPLATE_TYPEDEF(x, y) %template(y) x; %typemap_output_ptr(x)
#define SWIG_ALLOW_OUTPUT_SIMPLE(x) %typemap_output_simple(x)
#define SWIG_INPUT INPUT
#define SWIG_OUTPUT OUTPUT
#define SWIG_INOUT(x) INOUT
#define SWIG_NAMED_OUTPUT(x) OUTPUT
#define SWIG_VOID(x) void
#define SWIG_PYOBJECT(...) PyObject*
#else
#define SWIG_IGNORE(x)
#define SWIG_AUTODOC
#define SWIG_IGNORE_ENUMS(x)
#define SWIG_HASH_FUNC(class,func)
#define SWIG_EXTEND(x, code)
#define SWIG_TEMPLATE_TYPEDEF(x, y)
#define SWIG_ALLOW_OUTPUT_SIMPLE(x)
#define SWIG_INPUT
#define SWIG_OUTPUT
#define SWIG_INOUT(x) x
#define SWIG_NAMED_OUTPUT(x) x
#define SWIG_VOID(x) x
#define SWIG_PYOBJECT(...) __VA_ARGS__
#endif  // SWIG

#endif  // __lib_python_swig_h
