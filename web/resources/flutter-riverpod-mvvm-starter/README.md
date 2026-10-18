# Flutter + Riverpod + go_router MVVM starter

This starter is the `lib/` layer for an Android, iOS, or Web app. Let the official Flutter CLI create platform folders and generated files, then copy this `lib/` directory into that app. The sample is an offline counter: repository → view model → view, with Riverpod providers and a `go_router` route.

## Create and run

```sh
flutter create --empty starter_app
cd starter_app
# Copy this bundle's lib/ directory into the new project, replacing only its lib/ folder.
# Merge the flutter_riverpod and go_router constraints from this bundle's pubspec.yaml.
flutter pub get
flutter run -d chrome
```

Use `flutter devices` to choose an Android/iOS device or emulator. Building for iOS requires macOS and Xcode; Android builds require the Android toolchain. Keep the generated platform directories and project metadata from `flutter create`.

Package constraints were checked on 2026-10-18: `flutter_riverpod ^3.4.3` and `go_router ^18.1.0`. Recheck the official package pages before upgrading or locking a production app.
