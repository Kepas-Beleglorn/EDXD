{ pkgs ? import <nixpkgs> {}, python ? python3 }:
let
  my-python-pkg = python.pkgs.buildPythonPackage rec {
    pname = "ed-eXploration-dashboard";
    version = "v0.8.0.0";

    src = pkgs.fetchFromGitHub {
      owner = "Kepas-Beleglorn";
      repo = "EDXD";
      rev = version;
      hash = "sha256-d1bHkqeK3uX49QY5QqNklhjNEZ1Xc2BAQIsDPedbTtg=";
    };

    preBuild = ''
      echo 'VERSION = "${version}"' > EDXD/_version.py
    '';

    # do not run tests
    doCheck = false;

    # specific to buildPythonPackage, see its reference
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
      python.pkgs.wxpython  # Use the overridden wxpython from the flake
      python.pkgs.filelock
    ];

    propagatedBuildInputs = [
      python.pkgs.tomli
      python.pkgs.watchdog
      python.pkgs.wxpython  # Use the overridden wxpython from the flake
      python.pkgs.filelock
    ];
  };
in
  my-python-pkg
  