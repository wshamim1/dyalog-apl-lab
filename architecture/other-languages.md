# Dyalog and other languages

How code in Python, C#, C and C++ can work with the Dyalog runtime. The short
version: **Python runs as a separate program that talks to Dyalog; .NET and C
code run inside the Dyalog process. In every case Dyalog uses compiled code or
a connection, never raw source in another language.**

| Language | Where it runs | How it connects | Used in this repo |
| --- | --- | --- | --- |
| Python | a separate process | RIDE protocol, HTTP, or Py'n'APL | Streamlit app, Jupyter kernel, MySQL bridge, Jarvis clients |
| C# / .NET | inside Dyalog | `⎕USING`: a compiled `.dll` | not yet |
| C | inside Dyalog | `⎕NA`: a compiled shared library | Kafka (`librdkafka`) |
| C++ | inside Dyalog | `⎕NA`, through `extern "C"` functions | Kafka (`kafka.so` wraps librdkafka) |

## Python: two programs talking

Python and Dyalog are separate processes. They exchange text (APL code or JSON)
over a connection, and neither can see the other's variables directly.

| In this repo | How Python reaches Dyalog |
| --- | --- |
| [dyalog_ride](../integrations/dyalog_ride/README.md) (Streamlit app, MySQL bridge) | the **RIDE protocol** over TCP 4502, the same as the RIDE editor |
| [Jupyter kernel](../notebooks/README.md) | also **RIDE**: the kernel is Python, and it starts and drives its own Dyalog |
| [Jarvis clients](../integrations/jarvis/README.md) | **HTTP/JSON** to APL functions |

Dyalog also offers **Py'n'APL**, a bridge library that lets APL call Python
(and the other way round), with arrays converted automatically. It's still
two processes underneath.

## C# and .NET: compiled assemblies, in-process

Dyalog has built-in .NET support. It loads **compiled** .NET assemblies
(`.dll`) and calls their public classes as if they were APL namespaces. It
doesn't compile C# source.

1. Compile the C# with the usual tools:

   ```csharp
   // MyLib/Calc.cs
   namespace MyLib {
       public static class Calc {
           public static double Average(double[] xs) => System.Linq.Enumerable.Average(xs);
           public static string Greet(string name) => $"Hello, {name}!";
       }
   }
   ```

   ```sh
   dotnet build          # → MyLib.dll
   ```

2. Load it and call it from APL:

   ```apl
         ⎕USING←'MyLib,/path/to/MyLib.dll'     ⍝ namespace, then the DLL's path
         Calc.Greet ⊂'Ann'
   Hello, Ann!
         Calc.Average ⊂1 2 3 4                 ⍝ ⊂: the whole vector is one argument
   2.5
   ```

   .NET's own libraries work the same way: `⎕USING←'System'`, then
   `Math.Sqrt 2` or `DateTime.Now`.

- **Values:** numbers, text and arrays convert automatically (`double`,
  `string`, `double[]`…). Objects come back as references you use from APL:
  `obj.Method`, `obj.Property`, `⎕NEW`.
- **Public only:** whatever the assembly makes public is callable.
- **Requirements:** a .NET runtime (6 or 8) where Dyalog runs, and Dyalog's
  .NET support (Dyalog.Net.Bridge) enabled. The containers in this repo don't
  include .NET. See Dyalog's .NET documentation for the setup on Linux.

## C and C++: shared libraries via `⎕NA`

`⎕NA` (Name Association) declares a function in a compiled shared library, and
then APL calls it like any APL function.

1. Compile the code into a shared library:

   ```c
   // mymath.c
   int add(int a, int b) { return a + b; }
   double average(const double *xs, int n) {
       double s = 0; for (int i = 0; i < n; i++) s += xs[i]; return s / n;
   }
   ```

   ```sh
   gcc -shared -fPIC -o libmymath.so mymath.c   # Linux; macOS .dylib, Windows .dll
   ```

2. Declare each function's C types, then call it:

   ```apl
         ⎕NA 'I4 /path/libmymath.so|add I4 I4'           ⍝ returns int; takes 2 ints
         add 2 3
   5
         ⎕NA 'F8 /path/libmymath.so|average <F8[] I4'     ⍝ <F8[]: array of doubles in
         average (1 2 3 4) 4
   2.5
   ```

   The type codes: `I4` is an int, `F8` a double, `0T1` a string. `<` marks an
   input, `>` an output, and `[]` an array.

- **C++ needs `extern "C"`.** `⎕NA` calls plain C-style functions. C++
  "mangles" function names and has classes, so expose C functions that call
  your C++ code:

  ```cpp
  extern "C" double average(const double *xs, int n) { /* call your C++ here */ }
  ```

  This is exactly how Dyalog's Kafka library works: `kafka.so` is C++ with
  `extern "C"` functions around librdkafka, declared with `⎕NA` in
  [vendor/aplsource/kafka/NA.aplf](../integrations/kafka/vendor/aplsource/kafka/NA.aplf).
- **Build for the platform Dyalog runs on.** Dyalog here runs in a **Linux**
  container, so build a Linux `.so`, not a macOS library. Libraries it depends
  on must be in the container too: the Kafka image needed `libsasl2`.
- **There's no safety net.** A bug in C, such as writing past the end of an
  array, can crash the whole Dyalog process. APL errors are caught; C crashes
  aren't.
- **The declaration must match the real function exactly.** A wrong `⎕NA`
  type gives wrong results or a crash.

## What doesn't work

Pasting C#, C or C++ **source** into Dyalog doesn't work. Dyalog runs APL; for
other languages it loads **compiled** code (`⎕USING`, `⎕NA`) or talks to
another **running program** (Python over RIDE or HTTP).

> The C# and C examples on this page show the standard `⎕USING` and `⎕NA`
> patterns. Unlike the rest of the repo, they haven't been run here: the
> containers have no .NET runtime or C compiler. `⎕NA` itself is tested here
> indirectly, through the Kafka integration.
