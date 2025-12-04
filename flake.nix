{
  description = "EDXD devshell with Wayland + X11/XCB + zlib";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:nix-community/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
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
        project = pyproject-nix.lib.project.loadPyproject {
          # Read & unmarshal pyproject.toml relative to this project root.
          # projectRoot is also used to set `src` for renderers such as buildPythonPackage.
          projectRoot = ./.;
        };

        python = pkgs.python3;
      in
      {
        devShells.default = pkgs.mkShell {
          inherit buildInputs LD_LIBRARY_PATH;
        };
        packages.default =
          let
            # Returns an attribute set that can be passed to `buildPythonPackage`.
            attrs = project.renderers.buildPythonPackage { inherit python; };
          in
          # Pass attributes to buildPythonPackage.
          # Here is a good spot to add on any missing or custom attributes.
          python.pkgs.buildPythonPackage (
            attrs
            // {
              env.CUSTOM_ENVVAR = "hello";
            }
          );
      }
    );
}
