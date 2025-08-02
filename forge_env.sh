export FORGE_PROJECT_ROOT="$(realpath $(dirname $(realpath $0)))/.."

validate_variable() {
  local var_name="$1" default_value="$2" value

  # indirect expansion to get the current value of $var_name
  eval "value=\${$var_name:-}"

  if [[ -z $value ]]; then
    # not set or empty → assign default
    eval "export $var_name=\"\$default_value\""
  elif [[ ! -d "$value" ]]; then
    # set but not a valid dir → error out
    echo "Error: $var_name is set to an invalid path: $value" >&2
  fi
}

validate_variable "JAVA_HOME" "/usr/lib/jvm/java-17-openjdk/"
validate_variable "ANDROID_SDK_ROOT" "$FORGE_PROJECT_ROOT/Android/Sdk"

export PATH=${FORGE_PROJECT_ROOT}/apache-maven-3.8.1/bin:${PATH}
