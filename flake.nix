{
  description = "Python development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          flask
          requests
          waitress
          python-dotenv
          pyyaml
          
          # Development tools
          pip
          black
          flake8
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
          ];

          shellHook = ''
            # Create and activate virtual environment if it doesn't exist
            if [ ! -d "venv" ]; then
              python -m venv venv
            fi
            source venv/bin/activate
            
            # Set environment variables
            export PYTHONPATH="$PWD:$PYTHONPATH"
            echo "Python development environment activated!"
          '';
        };
      });
} 