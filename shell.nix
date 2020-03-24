{ nixpkgs ? import <nixpkgs> { } }:

with import <nixpkgs> { };

let channels = rec {
  #requirements = import ./nix/requirements.nix { }; 
  requirements_cadCAD = import ./nix/cadCAD/requirements.nix { }; 
};
in with channels;

let start-server = pkgs.writeShellScriptBin "start-server" ''
    ./start.sh
  '';
in
let start-app = pkgs.writeShellScriptBin "start-app" ''
    cd app && yarn start
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
    source venv/bin/activate
  '';
}
