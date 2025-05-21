{ pkgs ? import <nixpkgs> {}, isDev ? true }:

pkgs.mkShell {
  packages = with pkgs; if isDev then [
    python312
    python312Packages.pip
    python312Packages.virtualenv
  ] else [];

  shellHook = 
    let venvPath = "$HOME/venv/homelab"; 
        preproduction = if isDev then "true" else "false";
        remoteHost = "hetzner";
  in ''
    ${ if isDev then ''
      export PREPRODUCTION=${preproduction}

      if [ ! -d ${venvPath} ]; then
        python -m venv ${venvPath}
      fi
      source ${venvPath}/bin/activate
      pip install -r requirements.txt

      python app.py && exit 
    '' else ''
      rsync -avP --delete ./ ${remoteHost}:/root/homelab-dashboard --exclude .git
      ssh ${remoteHost} "cd /root/homelab-dashboard && docker compose down && docker compose up -d --build"
      exit
    ''
    }
  '';
}
