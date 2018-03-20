require "open-uri"
require "fileutils"
require "pry"

f = open("https://git.kernel.org/pub/scm/docs/man-pages/man-pages.git/plain/man7/signal.7")

found = false
header = "Signal    Value  Action Comment"
signals_file = open("pages/signals", "w")
signal_file = nil
f.each do |line|
  if line.match(/Signal\tValue\tAction\tComment/)
    found = true
    next
  end
  next unless found
  if line.match(/^\.TE/)
    found = false
    next
  end
  line.gsub!(/\\fB|\\P|\\fP|\\/, "")
  name, num, action, description = line.split("\t")
  signals_file.puts("#{name.ljust(9)} #{num.ljust(8)} #{action.ljust(4)} #{description}")
  if name != ""
    filename = "pages/#{name}"
    signal_file = open(filename, "w")
    signal_file.puts("Value  Action Comment")
    FileUtils.ln_sf filename, filename.downcase
  end
  unless signal_file.nil?
    signal_file.puts("#{num.ljust(8)} #{action.ljust(4)} #{description}")
  end
end

