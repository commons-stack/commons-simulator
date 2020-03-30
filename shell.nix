{ nixpkgs ? import <nixpkgs> { } }:

with import <nixpkgs> { };

let channels = rec {
  #requirements_cadCAD = import ./nix/cadCAD/requirements.nix { }; 
};
in with channels;

let start-server = pkgs.writeShellScriptBin "start-server" ''
    ./start.sh
  '';
in
let start-app = pkgs.writeShellScriptBin "start-app" ''
    cd app && npx react-scripts start
  '';
in
let start = pkgs.writeShellScriptBin "start" ''
  start-server & start-app && fg
'';
in
let
  pkgs = [
    start
    start-server
    start-app

    python36
    python36Packages.pip
    python36Packages.setuptools
    python36Packages.virtualenvwrapper
    python36Packages.matplotlib
    python36Packages.scipy
    nodejs-12_x
    yarn
    pkg-config
    gcc
  ];
in nixpkgs.stdenv.mkDerivation {
  name = "env";
  buildInputs = [ pkgs ];
  shellHook = ''
    export SOURCE_DATE_EPOCH=315532800
    if [ ! -d "venv" ]; then
      virtualenv venv
      source venv/bin/activate
      python -m pip install -r requirements.txt
    else
      source venv/bin/activate
      python -m pip install -r requirements.txt
    fi
  '';
}
