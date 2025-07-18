# dvt — Developer‑Tools Launcher

A tiny CLI that lets each **git repository** ship its own helper scripts
(without committing them) while keeping everything in a single, tidy
`~/dev‑tools` workspace.

```
repo/                  # your project
└─ .devtools -> ~/dev-tools/repo/   # symlink managed by dvt
   ├─ build-fw         # any executable helpers
   └─ flash-prod
```

Helpers appear on **`$PATH` only when you’re inside that repo**, update
automatically when you `cd`, and shadow outer‑repo helpers in nested
checkouts.

---

## 🌱 Quick start

```bash
# 0.
python3 -m venv ~/.venvs/cli
source ~/.venvs/cli/bin/activate          # add this line to ~/.bashrc if you like
python -m pip install --upgrade pip       # always good hygiene

# 1. install
pip install dvt     # add [completion] extra later if you want tab‑completion

# 2. create the global workspace
dvt init

# 3. install the shell hook once per machine
dvt install-hook && exec $SHELL      # reloads your shell

# 4. per‑repo bootstrap
cd ~/Code/my‑project
dvt link

# 5. add your first helper
dvt new build-fw
vim .devtools/build-fw   # write the script; save & make executable

build-fw                 # runs immediately (hook already injected)
```

---

## 🛠  Available commands  (`dvt -h`)

| Command | What it does |
|---------|--------------|
| `init`            | create `~/dev‑tools` (or `$DVT_HOME`) |
| `link`            | symlink `.devtools` in the current repo |
| `new <name>`      | scaffold a new helper script |
| `ls`              | list helpers visible from *this* directory |
| `shell-hook`      | print the Bash hook (for manual sourcing) |
| `install-hook`    | write hook to `~/.config/dvt/hook.bash` & source it |
| `uninstall-hook`  | remove the hook from rc files |
| `doctor`          | report broken links & non‑executable helpers |
| `help`            | mini manual (this content) |

---

## ⚙️ Workspace states

| State | Meaning | Command to advance |
|-------|---------|--------------------|
| **G0** | dvt not installed | `pip install dvt` |
| **G1** | workspace missing | `dvt init` |
| **G2** | no projects linked | `dvt link` in a repo |
| **G3** | helpers available | *normal work mode* |

---

## ✨ Tips

* Helpers can be **anything executable**: Bash, Python, Go, even Makefiles.
* `doctor` is safe to run from anywhere—checks the whole workspace.
* To move the workspace: `export DVT_HOME=/path` *before* `dvt init`.
* Want tab‑completion? `pip install "dvt[completion]"` then rerun `dvt install-hook`.