# Setup on a fresh host

The repo is the complete project state - but git configuration is not part of the
cloned content. After cloning on a new machine, re-apply the identity and
credential settings below so this project stays isolated from any other account
on that machine (spec section 12).

## 1. Clone

    git clone https://github.com/claudenstein1/claudenstein.git
    cd claudenstein

## 2. Repo-local git identity

Keeps commits attributed to the dedicated account, not any personal identity that
also uses git on the host.

    git config user.name "claudenstein1"
    git config user.email "claudenstein1@gmail.com"

## 3. Credential isolation

Keys this repo's credential by full path, so it gets its own token slot and does
not reuse (or overwrite) any personal github.com login on the same machine.

    git config credential.useHttpPath true

Authenticate as claudenstein1 on first push. Use a fine-grained Personal Access
Token created while logged in as claudenstein1, scoped to this repo only, with
Contents: Read and write. Do not store any other credential on the host.

## 4. Python environment (build123d NOT required yet)

    python -m venv .venv
    # Windows:
    .venv/Scripts/activate
    # POSIX:
    # source .venv/bin/activate

    pip install -e .            # core only: pyyaml, pytest

build123d (CAD geometry validation) is deliberately deferred. Install it only
when a cycle is about to commit a build123d design:

    pip install -e .[cad]      # adds build123d (heavy: OCP/OpenCascade)

## 5. Validate

    make validate

This is green without build123d; the geometry tests skip until it is installed.

## 6. Pick up the work

Read, in order: genome.md (the constitution), CLAUDE.md (how to run a cycle), and
docs/status.md (current state, decision log, open items). Everything needed to
continue is in the repo.
