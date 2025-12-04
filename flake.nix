{
  description = "EDXD devshell with Wayland + X11/XCB + zlib";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python3;
      in {
        devShells.default = pkgs.mkShell {
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
          ];

          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.wayland
            pkgs.libxkbcommon
            pkgs.gtk3
            pkgs.glib
            pkgs.xorg.libxcb
            pkgs.zlib
          ];
        };

        packages = rec {
          edxd = python.pkgs.callPackage ./default.nix {};
          default = edxd;
        };
      }
    );
}
