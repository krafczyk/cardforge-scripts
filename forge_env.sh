export FORGE_PROJECT_ROOT="$(realpath $(dirname $(realpath $0)))/.."

validate_variable() {
  local var_name="$1"
  local default_value="$2"
  # indirect expansion to get the current value of $var_name
  local value="${!var_name:-}"

  if [[ -z "$value" ]]; then
    # not set or empty → assign default
    export "$var_name"="$default_value"
  elif [[ ! -d "$value" ]]; then
    # set but not a valid dir → error out
    echo "Error: $var_name is set to an invalid path: $value" >&2
    exit 1
  fi
}

validate_variable "JAVA_HOME" "/usr/lib/jvm/java-17-openjdk/"
validate_variable "ANDROID_SDK_ROOT" "$FORGE_PROJECT_ROOT/Android/Sdk"
