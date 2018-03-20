require "open-uri"
require "nokogiri"
require "pry"

page = Nokogiri::HTML(open("https://filippo.io/linux-syscall-table/"))
syscall_rows = page.css(".tbls-table > tr.tbls-entry-collapsed").map do |row|
  row.css("td").map(&:text).join("\t")
end
args_rows = page.css(".tbls-table > tr.tbls-arguments-collapsed").map do |row|
  sub_rows = row.css("tbody tr")
  row_text = []
  sub_rows[0].css("td").each_with_index do |register, i|
    row_text << "#{register.text.gsub(/%/, "")}: #{sub_rows[1].css("td")[i].text}"
  end
  row_text.join(" ")
end
  
syscall_rows.each_with_index do |syscall, i|
  puts "#{syscall}\n\t\t#{args_rows[i]}\n\n"
end 
