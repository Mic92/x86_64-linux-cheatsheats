with import <nixpkgs> {};

let
  # Replace this with your kernel version!
  kernel = linux;
in stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    bashInteractive
    ruby.devEnv
    libxml2
    #pandoc
    python3
  ];

  nativeBuildInputs = kernel.moduleBuildDependencies;

  hardeningDisable=["all"];

  KERNEL_DIR = "${kernel.dev}/lib/modules/${kernel.modDirVersion}/build";
}
