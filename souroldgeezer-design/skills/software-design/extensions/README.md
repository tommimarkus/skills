# Software Design Extensions

Extensions add stack-specific evidence and smell codes to the core software-design reference. They do not override the core rules in [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md).

Current extensions:

- [dotnet.md](dotnet.md) - .NET solution/project design signals.
- [java.md](java.md) - Java package/module/build/API design signals.
- [rust.md](rust.md) - Rust crate/workspace design signals.
- [shell-script.md](shell-script.md) - Bash/zsh shell-script design signals,
  including Linux, macOS, and WSL compatibility boundaries.
- [python.md](python.md) - Repo-internal Python tooling design signals
  (scripts, dev tools, CI helpers, generators, validators); skips Python
  web/ASGI applications.

Add or expand an extension only when repeated pressure cases show the core
workflow plus a strong base model misses stack-specific design signals. Keep
extension claims about platform facts anchored to official runtime
documentation and design-goodness claims anchored to the core reference.
