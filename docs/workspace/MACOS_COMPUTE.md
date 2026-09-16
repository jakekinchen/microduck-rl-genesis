# Local compute and Python Dock entries

## Verified on 2026-09-05

The Codex task **Set up training stack roadmap** launched both the full
`tests/run_all.py` regression (PID 7511 at 18:39:25 CDT) and
`scripts/train_walking_viability.py --run-id walking-20260905-v9`
(PID 8462 at 18:41:28). The suite was still running when training began.
Its `smoke_env.py` child (PID 8634) and the trainer were simultaneously listed
by `lsappinfo` as `type="Foreground"`, both using uv's Python 3.12.12.
These are separate processes from one task; two icons do not imply two agents.

The installed Genesis `ext/pyrender/viewer.py` creates a hidden `tkinter.Tk`
on macOS during import, with a comment explaining that it avoids a crash.
It also imports `pyglet.window.Window`. Pyglet's Cocoa event-loop constructor
calls `NSApplication.setActivationPolicy_(Regular)`. These imports occur even
when the simulation is configured with `show_viewer=False`.

A fresh `PYGLET_SHADOW_WINDOW=false python -c 'import genesis; ...'` probe still
registered a Python application in Launch Services (PID 9161). The installed
Genesis viewer already sets `shadow_window=False` itself. That option is not
a verified Dock fix. No global Python, Dock, Tk, Pyglet, AppKit or backend
configuration was changed. Existing training and viewer processes were left
running.

## Launch discipline

Use `./scripts/duck verify` after tooling changes. It runs no simulator.
The full simulation suite checks occupancy before spawning any tests:

```sh
.venv-apple/bin/python tests/run_all.py
```

For training, chain the guard and the exact intended command conditionally:

```sh
./scripts/duck-ops guard && .venv-apple/bin/python scripts/TRAINER.py ARGS
```

`TRAINER.py ARGS` is a placeholder for the authorized experiment command.
Do not execute a guard and then launch unconditionally in a separate tool
call. Exit 3 means recognized compute is present; exit 2 means inspection
failed. Wait for the owner to finish, or continue independent offline work.

Activity reports label training, the full simulation suite and a bounded list
of known standalone simulator tests. New `train_*.py` scripts are recognized
without extending a trainer-name whitelist. Python module invocation and
common interpreter flags are recognized; filenames in inline code or arbitrary
data arguments are not treated as running training scripts. Command arguments
are not disclosed in reports.

The preflight is still an instantaneous advisory check, not a host reservation.
Simultaneous launches can race; direct commands can bypass it. Arbitrary
evaluators, wrappers, unlisted simulator tests and remote jobs are outside its
coverage. Its conservative host inventory can also show another checkout's
compute. The v1 `no_known_training_process` status is retained for compatibility
and means no recognized compute candidate; it does not prove host idleness.

## What this fixes and what remains

The guard can now see the full suite that was missed during the incident, and
the suite refuses to launch alongside recognized training. Existing physics,
rendering, action handling and experiment sources are unchanged. A successful
preflight or tooling test is not behavioral or physical validation.

A running trainer can still show one Python Dock icon. Rendering evaluations
can still create their own entries. Complete suppression needs a supported
background-application mode in Genesis/Tk/Pyglet, verified against simulation,
offscreen camera rendering and intentional interactive viewers. Do not switch
to EGL or remove the Tk initialization solely to hide icons: the former changes
the rendering platform and the latter removes an explicit macOS crash workaround.

Primary references:
- [Pyglet runtime options](https://docs.pyglet.org/en/latest/programming_guide/options.html)
- [Pyglet OpenGL shadow context](https://docs.pyglet.org/en/latest/programming_guide/context.html)
- [GLFW macOS initialization](https://www.glfw.org/docs/latest/intro): its menu-bar
  hint applies to GLFW initialization, not Genesis's Tk/Pyglet import path.
