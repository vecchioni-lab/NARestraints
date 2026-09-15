#!/usr/bin/env bash
# Build and test the wheel AND source distribution outside the source tree.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/narestraints-release.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH PYTHONHOME || true
python -m venv "$WORK/build"
"$WORK/build/bin/python" -m pip install build
(cd "$ROOT" && "$WORK/build/bin/python" -m build --outdir "$WORK/dist")
mapfile -t WHEELS < <(find "$WORK/dist" -maxdepth 1 -name '*.whl')
mapfile -t SDISTS < <(find "$WORK/dist" -maxdepth 1 -name '*.tar.gz')
[ "${#WHEELS[@]}" = 1 ] && [ "${#SDISTS[@]}" = 1 ]
for kind in wheel sdist; do
  ARCHIVE="${WHEELS[0]}"
  [ "$kind" != sdist ] || ARCHIVE="${SDISTS[0]}"
  python -m venv "$WORK/$kind"
  PY="$WORK/$kind/bin/python"
  "$PY" -m pip install "$ARCHIVE" pytest
  "$PY" -m pip check
  mkdir "$WORK/test-$kind"
  cp -R "$ROOT/tests" "$ROOT/examples" "$WORK/test-$kind/"
  (cd "$WORK/test-$kind" && "$PY" -I -m pytest -q --import-mode=importlib tests)
  (cd "$WORK/test-$kind" && "$PY" -I "$ROOT/scripts/check_installed.py" \
    --source-root "$ROOT" --expected-version 1.1.2)
done
mkdir -p "$ROOT/dist"
cp "$WORK/dist/"* "$ROOT/dist/"
(cd "$ROOT/dist" && sha256sum ./*.whl ./*.tar.gz > SHA256SUMS)
printf 'Release verification passed: wheel and sdist, installed outside checkout.\n'
