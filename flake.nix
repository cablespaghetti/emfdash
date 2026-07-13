{
  description = "Dev shell using external derivation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        mypackage = pkgs.python3Packages.callPackage ./. {
          lib = pkgs.lib;
        };
      in
      {
        #packages.default = pkgs.mkShell { buildInputs = [ (pkgs.python3Packages.python.withPackages (p: [ mypackage ])) ]; };
        packages.default = mypackage;
      }
    );
}
