require "open-uri"
require "nokogiri"
require "pry"
require 'tempfile'
require 'fileutils'

url = "http://www.felixcloutier.com/x86"
page = Nokogiri::HTML(open(url))
open("pages/instructions", "w+") do |f|
  text = page.css("table tr").map do |row|
    columns = row.css("td")
    next if columns.size < 2
    [columns[0].text.strip.ljust(15), columns[1].text.strip].join(" ")
  end.join("\n")
  f.puts text
end

page.css("table tr td a").map do |a|
  filename = a.text.gsub(/ /, "-")
  path = "pages/#{filename}"
  FileUtils.ln_sf filename, "pages/#{filename.downcase}"
  next if File.exists? path
  file = Tempfile.new('foo')
  url = URI::join("http://www.felixcloutier.com/x86/", a["href"].strip.gsub(/ /, ""))
  file.write open(url).read
  file.flush
  puts ["pandoc", file.path, "--from=html", "--to=plain", "-o", path].join(" ")
  system("pandoc", file.path, "--from=html", "--to=plain", "-o", path)
  file.close
end
