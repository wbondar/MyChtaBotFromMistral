{ pkgs }:

let
  deps = [
    pkgs.python311Packages.schedule
    pkgs.python311Packages.python-telegram-bot
    pkgs.python311Packages.selenium
    pkgs.chromium
    pkgs.chromedriver
    pkgs.unzip
  ];
in
pkgs.mkShell {
  buildInputs = deps;
}
