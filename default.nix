{
  fetchFromGitHub,
  buildPythonPackage,
  setuptools,
  wheel,

  # Wayland / GTK stack
  wayland,
  libxkbcommon,
  gtk3,
  glib,
  nss,
  nspr,
  cairo,
  pango,
  harfbuzz,

  # X11 / XCB stack
  xorg,

  # zlib (libz.so.1)
  zlib,

  # Requirements
  tomli,
  watchdog,
  wxpython,
  filelock,
}:
buildPythonPackage rec {
  pname = "ed-eXploration-dashboard";
  version = "v0.5.0.6";

  src = fetchFromGitHub {
    owner = "Otard95"; # "Kepas-Beleglorn";
    repo = "EDXD";
    rev = version;
    hash = "sha256-zOI4zVpkfJvs0L+sjqeGSrXHl4QCd4IPi/EJ0Z9O6bo=";
  };

  # do not run tests
  doCheck = false;

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  build-system = [
    setuptools
    wheel
  ];

  buildInputs = [
    # Wayland / GTK stack
    wayland
    libxkbcommon
    gtk3
    glib
    nss
    nspr
    cairo
    pango
    harfbuzz

    # X11 / XCB stack
    xorg.libX11
    xorg.libXcursor
    xorg.libXrandr
    xorg.libXi
    xorg.libXrender
    xorg.libXext
    xorg.libXfixes
    xorg.libxcb
    xorg.xcbutil
    xorg.xcbutilimage
    xorg.xcbutilkeysyms
    xorg.xcbutilwm

    # zlib (libz.so.1)
    zlib

    # Requirements
    tomli
    watchdog
    wxpython
    filelock
  ];

  propagatedBuildInputs = [
    tomli
    watchdog
    wxpython
    filelock
  ];

  # installPhase = ''
  #   mkdir -p $out/bin
  #   cp ed-eXploration-dashboard $out/bin
  # '';
}
