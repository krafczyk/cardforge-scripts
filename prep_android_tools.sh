source "$(dirname $(realpath $0))/forge_env.sh"

mkdir -p "${ANDROID_SDK_ROOT}"

# Check if sdkmanager is already installed
if [ $(which sdkmanager 2>/dev/null | wc -l) -eq 0 ]; then
  pacaur -S --noconfirm android-sdk-cmdline-tools-latest
else
  echo "sdkmanager already installed."
fi

# Install SDK 35
unset JAVA_HOME
sdkmanager --sdk_root="${ANDROID_SDK_ROOT}" "platforms;android-35" "build-tools;35.0.0" "platform-tools"

source "$(dirname $(realpath $0))/forge_env.sh"

# Install old maven
cd ${FORGE_PROJECT_ROOT}
curl -o apache-maven-3.8.1-bin.tar.gz https://archive.apache.org/dist/maven/maven-3/3.8.1/binaries/apache-maven-3.8.1-bin.tar.gz
tar xf apache-maven-3.8.1-bin.tar.gz

# Install android maven plugin
PLUGIN_VER=4.6.2
#plugin_dir="${HOME}/.m2/repository/com/simpligility/maven/plugins/android-maven-plugin/${PLUGIN_VER}"
plugin_dir="${FORGE_PROJECT_ROOT}/maven_cache/com/simpligility/maven/plugins/android-maven-plugin/${PLUGIN_VER}"
mkdir -p "${plugin_dir}"
rm -rf "${plugin_dir}"/*
cd "${plugin_dir}"
wget -O "android-maven-plugin-${PLUGIN_VER}.jar" "https://github.com/Card-Forge/android-maven-plugin/releases/download/${PLUGIN_VER}/android-maven-plugin-${PLUGIN_VER}.jar"
wget -O "android-maven-plugin-${PLUGIN_VER}.pom" "https://github.com/Card-Forge/android-maven-plugin/releases/download/${PLUGIN_VER}/android-maven-plugin-${PLUGIN_VER}.pom"
