'''
WikiLinks Extension for Python-Markdown
======================================

Converts [[WikiLinks]] to relative links.

See <https://Python-Markdown.github.io/extensions/wikilinks>
for documentation.

Original code Copyright [Waylan Limberg](http://achinghead.com/).

All changes Copyright The Python Markdown Project

License: [BSD](https://opensource.org/licenses/bsd-license.php)

'''

from markdown import Extension
from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree
import re
import os

def build_url(label):
	""" Build a url from the label, a base, and an end. """
	#clean_label = re.sub(r'([ ]+_)|(_[ ]+)|([ ]+)', '_', label)
	list = label.split('|')
	url = list[0]
	if len(list) == 1:
		url = label
	else:
		label = list[1]
	return (url, label)

def find_article(label):
	list = label.split('#')
	return os.path.isfile(os.path.join(os.getcwd(), "articles", list[0], "article.json"))

class WikiLinkPlusExtension(Extension):

	def __init__(self, **kwargs):
		self.config = {
			'base_url': ['/', 'String to append to beginning or URL.'],
			'end_url': ['/', 'String to append to end of URL.'],
			'exist_class': ['wikilink', 'CSS hook. Leave blank for none.'],
			'not_exist_class' : ['ne_wikilink', 'CSS hook. Leave blank for none.'],
			'build_url': [build_url, 'Callable formats URL from label.'],
			'find_article': [find_article, 'Callable'] 
		}

		super().__init__(**kwargs)

	def extendMarkdown(self, md):
		self.md = md

		# append to end of inline patterns
		#WIKILINK_RE = r'\[\[([\w0-9_ -]+)\]\]'
		WIKILINK_RE = r'\[\[([^[\]*?\"<>]+)\]\]'
		wikilinkPattern = WikiLinksInlineProcessor(WIKILINK_RE, self.getConfigs())
		wikilinkPattern.md = md
		md.inlinePatterns.register(wikilinkPattern, 'wikilink', 75)


class WikiLinksInlineProcessor(InlineProcessor):
	def __init__(self, pattern, config):
		super().__init__(pattern)
		self.config = config

	def handleMatch(self, m, data):
		if m.group(1).strip():
			base_url, end_url, html_class, not_exist_class = self._getMeta()
			label = m.group(1).strip()
			config = self.config['build_url'](label)
			title = config[0]
			url = '/view/' + title
			a = etree.Element('a')
			a.text = config[1]
			a.set('href', '' + url)
			if html_class:
				a.set('class', html_class)
			if not_exist_class:
				if not self.config['find_article'](title):
					a.set('class', html_class + ' ' + not_exist_class)
		else:
			a = ''
		return a, m.start(0), m.end(0)

	def _getMeta(self):
		""" Return meta data or config data. """
		base_url = self.config['base_url']
		end_url = self.config['end_url']
		exist_class = self.config['exist_class']
		not_exist_class = self.config['not_exist_class']
		if hasattr(self.md, 'Meta'):
			if 'wiki_base_url' in self.md.Meta:
				base_url = self.md.Meta['wiki_base_url'][0]
			if 'wiki_end_url' in self.md.Meta:
				end_url = self.md.Meta['wiki_end_url'][0]
			if 'wiki_exist_class' in self.md.Meta:
				exist_class = self.md.Meta['wiki_exist_class'][0]
			if 'wiki_not_exist_class' in self.md.Meta:
				not_exist_class = self.md.Meta['wiki_not_exist_class'][0]
		return base_url, end_url, exist_class, not_exist_class


def makeExtension(**kwargs):  # pragma: no cover
	return WikiLinkPlusExtension(**kwargs)
