#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${COOP_JAVA_HOME:-}" ]]; then
  task_javac="$COOP_JAVA_HOME/bin/javac"
elif [[ -x .tools/jdk-17.0.20.1+1/bin/javac ]]; then
  task_javac=.tools/jdk-17.0.20.1+1/bin/javac
else
  task_javac=javac
fi
mkdir -p build/paper-classes
python3 java-paper/build_identity.py prepare
"$task_javac" --release 17 -cp vendor/mason.20.jar -d build/paper-classes \
  upstream/multiplex/Agents/*.java java-paper/paper/*.java java-paper/agents/*.java java-paper/policies/*.java
python3 java-paper/build_identity.py finish
