{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
  ];

  shellHook = ''
    export VENV_PATH=~/venv/homelab
    export PREPRODUCTION=true

    if [ ! -d $VENV_PATH ]; then
      python -m venv $VENV_PATH
    fi
    source $VENV_PATH/bin/activate
    pip install -r requirements.txt
    
    python app.py
  '';
}
