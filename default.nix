with import <nixpkgs> {};

let
  # Replace this with your kernel version!
  kernel = linux;
  #kernel_i686 = pkgsi686Linux.linux;

in stdenv.mkDerivation {
  name = "env";
  buildInputs = [
    bashInteractive
    (ruby.withPackages (ps: with ps; [ nokogiri pry ]))
    libxml2
    pandoc
    python3
  ];

  nativeBuildInputs = kernel.moduleBuildDependencies;

  hardeningDisable=["all"];

  KERNEL_DIR = "${kernel.dev}/lib/modules/${kernel.modDirVersion}/build";
  #KERNEL_I686_DIR = "${kernel.dev}/lib/modules/${kernel.modDirVersion}/build";
}
