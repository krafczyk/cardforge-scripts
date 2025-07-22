set -euo pipefail

source "$(dirname $(realpath $0))/forge_env.sh"
#export _JAVA_OPTIONS="-Xmx2g" # RAM for dexing

# Two phase build
# first build core components
mvn clean install \
  -Dmaven.test.skip=true \
  -Dmaven.repo.local="${FORGE_PROJECT_ROOT}/maven_cache"

#mvn install -Dmaven.test.skip=true
#mvn dependency:tree

# 2nd part build the android GUI
#unset JAVA_HOME
#export MAVEN_OPTS="--add-exports java.base/sun.security.pkcs=ALL-UNNAMED --add-exports java.base/sun.security.x509=ALL-UNNAMED"
# Build unsigned apk because of incompatibility with JDK 21 and the plugin
#  -U -B -P android-debug android:deploy install -e \

#cd "${FORGE_PROJECT_ROOT}/forge/forge-gui-mobile"

#mvn \
#  -U -B -P forge-gui-mobile-dev -e \
#  -Dmaven.repo.local="${FORGE_PROJECT_ROOT}/maven_cache" \
#  -Dandroid.sdk.path="$ANDROID_SDK_ROOT" \
#  -Dandroid.buildToolsVersion=35.0.0 \
#  -Dmaven.test.skip=true

## Get the APK file
#UNSIGNED_APK=$(find forge-gui-android/target -name "forge-android-*-debug-unsigned.apk" | head -n 1)
##ALIGNED_APK="${UNSIGNED_APK:0:-4}-aligned.apk"
#SIGNED_APK="${UNSIGNED_APK/-unsigned/-signed}"

#export PATH="$ANDROID_SDK_ROOT/build-tools/35.0.0:$PATH"

## Align
#zipalign -p 4 "$UNSIGNED_APK" "$SIGNED_APK"
## Sign
#apksigner sign \
#  --ks ~/.android/debug.keystore \
#  --ks-pass pass:android \
#  "$SIGNED_APK"
