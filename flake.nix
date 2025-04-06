{
  description = "python development flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          pillow
        ]);
      in
      {
        devShells = {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              pythonEnv
              ruff
              pyright
            ];
          };
        };
      }
    );
}
