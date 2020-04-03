#ifndef __E_ERROR__
#define __E_ERROR__

#include <string>
#include <map>       
#include <new>
#include <lib/base/sigc.h>

inline void segfault(void)
{
	*((char*)0)=0;
}

#ifndef NULL
#define NULL 0
#endif

#ifdef ASSERT
#undef ASSERT
#endif

#ifndef SWIG

#define CHECKFORMAT __attribute__ ((__format__(__printf__, 1, 2)))

/* eDebug adds newlines by itself, so calling eDebug("") may make sense. */
#pragma GCC diagnostic ignored "-Wformat-zero-length"

extern sigc::signal2<void, int, const std::string&> logOutput;
extern int logOutputConsole;

void CHECKFORMAT eFatal(const char*, ...) __attribute__((noreturn));
enum { lvlDebug=1, lvlWarning=2, lvlFatal=4 };

#ifdef DEBUG
    #define eDebug(...) do { printf(__VA_ARGS__); putchar('\n'); } while(0)
    #define eDebugNoNewLine(...) printf(__VA_ARGS__)
    #define eWarning(...) eDebug(__VA_ARGS__)
    #define ASSERT(x) { if (!(x)) eFatal("%s:%d ASSERTION %s FAILED!", __FILE__, __LINE__, #x); }
#else  // DEBUG
    inline void eDebug(const char* fmt, ...)
    {
    }

    inline void eDebugNoNewLine(const char* fmt, ...)
    {
    }

    inline void eWarning(const char* fmt, ...)
    {
    }
    #define ASSERT(x) do { } while (0)
#endif //DEBUG

#endif // SWIG

#endif // __E_ERROR__
