{ pkgs, python, src }:
let
  version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;
in
python.pkgs.buildPythonPackage {
  pname = "ed-eXploration-dashboard";
  inherit version src;

  preBuild = ''
    echo 'VERSION = "${version}"' > EDXD/_version.py
  '';

  doCheck = false;

  pythonRelaxDeps = [ "tomli" "filelock" ];
  nativeBuildInputs = [ python.pkgs.pythonRelaxDepsHook ];

  pyproject = true;
  build-system = [
    python.pkgs.setuptools
    python.pkgs.wheel
  ];

  buildInputs = [
    # Wayland / GTK stack
    pkgs.wayland
    pkgs.libxkbcommon
    pkgs.gtk3
    pkgs.glib
    pkgs.nss
    pkgs.nspr
    pkgs.cairo
    pkgs.pango
    pkgs.harfbuzz

    # X11 / XCB stack
    pkgs.xorg.libX11
    pkgs.xorg.libXcursor
    pkgs.xorg.libXrandr
    pkgs.xorg.libXi
    pkgs.xorg.libXrender
    pkgs.xorg.libXext
    pkgs.xorg.libXfixes
    pkgs.xorg.libxcb
    pkgs.xorg.xcbutil
    pkgs.xorg.xcbutilimage
    pkgs.xorg.xcbutilkeysyms
    pkgs.xorg.xcbutilwm

    # zlib (libz.so.1)
    pkgs.zlib

    # Requirements
    python.pkgs.tomli
    python.pkgs.watchdog
    python.pkgs.wxpython
    python.pkgs.filelock
  ];

  propagatedBuildInputs = [
    python.pkgs.tomli
    python.pkgs.watchdog
    python.pkgs.wxpython
    python.pkgs.filelock
  ];
}
