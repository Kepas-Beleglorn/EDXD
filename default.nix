{
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
buildPythonPackage {
  pname = "ed-eXploration-dashboard";
  version = "v0.5.0.3";

  src = ./.;

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


  # installPhase = ''
  #   mkdir -p $out/bin
  #   cp ed-eXploration-dashboard $out/bin
  # '';
}
