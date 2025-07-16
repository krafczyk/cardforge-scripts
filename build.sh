set -euo pipefail

source "$(dirname $(realpath $0))/forge_env.sh"

mvn install \
  -Dmaven.test.skip=true \
  -Dmaven.repo.local="${FORGE_PROJECT_ROOT}/maven_cache"
