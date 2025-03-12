# This script will build the native rust library and automatically copy it into a 
# bin directory. Currently it only works with dlls

cd native
cargo build --release
cd ..
cp native/target/release/native.dll bin/native.pyd