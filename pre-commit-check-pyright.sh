#!/bin/bash

# venvdir="$(realpath .pre-commit-venv)"
# if [[ ! -d "${venvdir}" ]]; then
#   python3 -m venv ${venvdir} || exit 1
# fi
# ${venvdir}/bin/pip install \
#   -r src/requirements.txt -r src/requirements-dev.txt || exit 1
# source ${venvdir}/bin/activate || exit 1
# ${venvdir}/bin/pyright \
#   --pythonversion 3.10 \
#   --pythonplatform Linux \
#   src/1e3ms-insights.py src/insights/ || exit 1

py_env=$(poetry -C $(pwd)/src env list --full-path | cut -f1 -d' ')
py="${py_env}/bin/python"
if [[ ! -e "${py}" ]]; then
  echo "could not find python executable"
  exit 1
fi

source ${py_env}/bin/activate
${py_env}/bin/pyright \
  --pythonversion 3.10 \
  --pythonplatform Linux \
  src/1e3ms-insights.py src/insights/ || exit 1
