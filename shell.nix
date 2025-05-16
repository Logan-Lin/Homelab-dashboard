{ pkgs ? import <nixpkgs> {}, isDev ? true }:

pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
  ];

  shellHook = 
    let venvPath = "$HOME/venv/homelab"; 
        preproduction = if isDev then "true" else "false";
        remoteHost = "hetzner";
  in ''
    export VENV_PATH=${venvPath}
    export PREPRODUCTION=${preproduction}

    if [ ! -d ${venvPath} ]; then
      python -m venv ${venvPath}
    fi
    source ${venvPath}/bin/activate
    pip install -r requirements.txt

    ${ if isDev then '' python app.py && exit '' else ''
      rsync -avP --delete ./ ${remoteHost}:/root/homelab-dashboard --exclude .git
      ssh ${remoteHost} "cd /root/homelab-dashboard && docker compose down && docker compose up -d --build"
      exit
    ''
    }
  '';
}
