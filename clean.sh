source "$(dirname $(realpath $0))/forge_env.sh"

mvn clean \
  -Dmaven.repo.local="${FORGE_PROJECT_ROOT}/maven_cache"
