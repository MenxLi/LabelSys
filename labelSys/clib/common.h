#ifndef LBLSYS_COMMON_H
#define LBLSYS_COMMON_H

#define FALSE 0
#define TRUE 1

#ifndef __cplusplus
typedef unsigned char bool;
#endif
typedef unsigned char uint8;


// Windows specific
// https://stackoverflow.com/questions/2164827/explicitly-exporting-shared-library-functions-in-linux
// https://stackoverflow.com/questions/24575348/wrapping-c-functions-in-python-with-ctypes-on-windows-function-not-found

#if defined(WIN32) || defined(_WIN32) || defined(__WIN32) && !defined(__CYGWIN__)
    #define EXPORT __declspec( dllexport )
    #define IMPORT __declspec(dllimport)
#elif defined(__GNUC__)
    //  GCC
    #define EXPORT __attribute__((visibility("default")))
    #define IMPORT
#else
    //  do nothing and hope for the best?
    #define EXPORT
    #define IMPORT
    #pragma warning Unknown dynamic link import/export semantics.
#endif

#endif
