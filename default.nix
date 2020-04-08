with import <nixpkgs> {};

let
  # Replace this with your kernel version!
  kernel = linux_latest;

  gems = bundlerEnv {
    name = "x86-cheatsheets";
    inherit ruby;
    gemdir = ./.;
  };
in stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    bashInteractive
    # when updating bundle
    #ruby.devEnv
    ruby
    gems
    libxml2
    pandoc
    python3
  ];

  nativeBuildInputs = kernel.moduleBuildDependencies;

  hardeningDisable=["all"];

  KERNEL_DIR = "${kernel.dev}/lib/modules/${kernel.modDirVersion}/build";
}
