outputs = { self, nixpkgs, flake-utils }:
  flake-utils.lib.eachDefaultSystem (system:
    let
      # Import nixpkgs with a custom overlay to override wxpython
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          (final: prev: {
            python3 = prev.python3.override {
              packageOverrides = python-prev: {
                wxpython = python-prev.wxpython.overrideAttrs (oldAttrs: {
                  version = "4.2.5";
                  src = final.fetchFromGitHub {
                    owner = "wxWidgets";
                    repo = "Phoenix";
                    rev = "wxPython-4.2.4";
                    hash = "sha256-44e836d1bccd99c38790bb034b6ecf70d9060f6734320560f7c4b0d006144793";
                  };
                  # wxPython 4.2.5 from GitHub source may need build flags
                  # Usually not needed for Phoenix, but kept for safety
                  buildInputs = oldAttrs.buildInputs or [];
                });
              };
            };
          })
        ];
      };

      # Use the overridden python3
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

          # Ensure the shell sees the overridden wxpython
          python.pkgs.wxpython
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
        # Pass the overridden pkgs to default.nix
        edxd = pkgs.callPackage ./default.nix { inherit pkgs python; };
        default = edxd;
      };
    }
  );
