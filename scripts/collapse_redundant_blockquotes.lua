-- Collapse blockquote wrappers that contain no content of their own.
--
-- Calibre sometimes uses nested <blockquote> elements purely for indentation.
-- Pandoc faithfully turns those wrappers into nested Markdown blockquotes, and
-- the print CSS then applies horizontal spacing once per level.  A wrapper
-- whose only block is another BlockQuote is structurally transparent, so it
-- can be removed without changing any text or a genuine nested quotation that
-- also contains outer-level paragraphs.
function BlockQuote(block)
  while #block.content == 1 and block.content[1].t == "BlockQuote" do
    block.content = block.content[1].content
  end
  return block
end
