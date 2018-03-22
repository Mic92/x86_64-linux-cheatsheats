with import <nixpkgs> {};
stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    bashInteractive
    ruby.devEnv
    libxml2
    pandoc
    python3
  ];
  hardeningDisable=["all"];
}
