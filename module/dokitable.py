from markdown import Extension
from markdown.blockprocessors import BlockProcessor

import collections
import xml.etree.ElementTree as etree
import re

pattern_attrib = re.compile(r'(\S\w*)(\s*=\s*([\'\"]([^\'\"]*)[\'\"]))?')
pattern_cell_div = re.compile(r'((!{2}|\|{2})[^|]*)((\|?)[^|])*')
pattern_cell_parse = re.compile(r'((!{2}|\|{2})[^|]*)')

class Parsed_data:
	full_text: str
	group: list[str]

	def __init__(self):
		self.group = []
	
	def from_match(self, m, capture_groups):
		self.full_text = m.group()
		groups = m.groups()
		for i in capture_groups:
			if i < len(groups):
				self.group.append(groups[i])

def parse_data(text: str, pattern: re.Pattern, list_type: type = list, split = 0, capture_groups = []):
	parsed_list = list_type()
	start = 0
	while True:
		m = pattern.search(text[start:])
		if m:
			if m.end() == 0:
				break
			data = Parsed_data()
			data.from_match(m, capture_groups)

			parsed_list.append(data)
			start += m.end()
		else:
			break

	if start < len(text):
		if split == 1:
			if len(parsed_list) > 0:
				parsed_list[-1].full_text += text[start:]
		elif split == 2:
			data = Parsed_data()
			data.full_text = text[start:]
			parsed_list.append(data)

	return parsed_list

def parse_attrib(text: str):
	attrib = parse_data(
		text = attrib_preprocess(text), 
		pattern = pattern_attrib,
		capture_groups = [0, 3]
	)
	return attrib

def attrib_preprocess(text: str):
	text = text.strip()
	text.replace('\"', '\" ')
	return text

def attrib_set(el: etree.Element, attrip_list: list[Parsed_data]):
	for a in attrip_list:
		if type(a.group[1]) != str:
			a.group[1] = ''
		el.set(a.group[0], a.group[1])
	return el

def parse_block(text_data):
	caption_split = text_data.split('|+')

	text_data = caption_split[0]

	caption_el = etree.Element('caption')
	if len(caption_split) > 1:
		caption_split_lines: list[str] = caption_split[1].split('\n')
		text_data += '\n'.join(caption_split_lines[1:])
		caption_data = caption_split_lines[0].split('|', 1)
		if len(caption_data) == 2:
			caption_attrip = parse_attrib(caption_data[0])
			caption_el = attrib_set(caption_el, caption_attrip)
			caption_el.text = caption_data[1].strip()
		else:
			caption_el.text = caption_data[0].strip()

	table_attrib: list[Parsed_data] = []

	row_split = text_data.split('|-')

	tbody_el = etree.Element('tbody')

	for i in range(len(row_split)):
		row_split_lines = row_split[i].split('\n')
		row_attrib: list[Parsed_data]

		row_el = etree.SubElement(tbody_el, 'tr')

		if i == 0:
			table_attrib = parse_attrib(row_split_lines[0])

		else:
			row_attrib = parse_attrib(row_split_lines[0])
			row_el = attrib_set(row_el, row_attrib)

		for j in range(1, len(row_split_lines)):
			cell_deq:collections.deque[Parsed_data] = parse_data(
				text = (row_split_lines[j][0] if len(row_split_lines[j]) > 0 else '') + row_split_lines[j],
				pattern = pattern_cell_div,
				list_type = collections.deque,
				split = 1
			)

			while len(cell_deq) > 0:
				cell_el = etree.SubElement(row_el, 'td')

				cell_data = cell_deq.popleft().full_text.strip()
				if cell_data[0] == '!':
					cell_el.tag = 'th'
				
				cell_split: list[Parsed_data] = parse_data(
					text = cell_data,
					pattern = pattern_cell_parse,
					split = 2
				)
				if len(cell_split) == 2:
					cell_attrib = parse_attrib(cell_split[0].full_text[2:])
					cell_el = attrib_set(cell_el, cell_attrib)
					cell_el.text = cell_split[-1].full_text[1:].strip()
				else:
					cell_el.text = cell_split[-1].full_text[2:].strip()

	output_caption = etree.tostring(caption_el, encoding = 'unicode')
	output =  output_caption + etree.tostring(tbody_el, encoding = 'unicode')

	return output, table_attrib

class DokiTableProcessor(BlockProcessor):

	RE_FENCE_START = r'^\s*\{\|\s*'
	RE_FENCE_END = r'\n\s*\|\}\s*$'

	def test(self ,parent, block):
		return re.match(self.RE_FENCE_START, block)
	
	def run(self, parent, blocks):
		original_block = blocks[0]
		blocks[0] = re.sub(self.RE_FENCE_START, '', blocks[0])

		for block_num, block in enumerate(blocks):
			if re.search(self.RE_FENCE_END, block):
				blocks[block_num] = re.sub(self.RE_FENCE_END, '', block)
				blocks[0], table_attrib = parse_block(blocks[0])
				table_el = etree.SubElement(parent, 'table')
				table_el = attrib_set(table_el, table_attrib)
				self.parser.parseBlocks(table_el, blocks[0:block_num + 1])
				for i in range(0, block_num + 1):
					blocks.pop(0)
				return True
		blocks[0] = original_block
		return False


class DokiTableExtension(Extension):
	def __init__(self, **kwargs):
		self.config = {
			'' : '',
			'de' : ''
		}

		super().__init__(**kwargs)
	
	def extendMarkdown(self, md):
		md.registerExtension(self)
		md.parser.blockprocessors.register(DokiTableProcessor(md.parser), 'dokitable', 1000)


