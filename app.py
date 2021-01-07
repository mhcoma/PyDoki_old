import datetime
import json
from module.dokitable import DokiTableExtension
import os

import flask
from flask import app

import markdown
from markdown.extensions.fenced_code import FencedCodeExtension

from module.tocplus import TocPlusExtension, do_nothing
from module.wikilinksplus import WikiLinkPlusExtension
from module.dokitable import DokiTableExtension

application = flask.Flask(__name__)

base_dir = os.path.dirname(__file__)

class Setting:
	def __init__(self):
		settings_filename = os.path.join(base_dir, 'settings', "settings.json")
		if os.path.isfile(settings_filename):
			settings_file = open(settings_filename, 'r', encoding = 'utf-8')
			settings = json.load(settings_file)
			settings_file.close()
		else:
			settings = {
				'wikiname' : 'WikiName',
				'url' : 'http://localhost',
				'mainpage' : 'MainPage',
				'language' : 'en_us'
			}
			settings_file = open(settings_filename, 'w', encoding = 'utf-8')
			settings_file.close()
		
		self.wikiname = settings['wikiname']
		self.url = settings['url']
		self.mainpage = settings['mainpage']
		self.language = settings['language']

	def get_language(self):
		language_filename = os.path.join(base_dir, 'languages', self.language + ".json")
		if os.path.isfile(language_filename):
			language_file = open(language_filename, 'r', encoding = 'utf-8')
			language = json.load(language_file)
			language_file.close()
		else:
			language = {}
		return language


class Article:
	def __init__(self, title, search = False, convert = False, history = False):
		self.raw_data = ""
		self.existence = False
		self.title = title

		self.directory_name = os.path.join(base_dir, 'articles', self.title)

		self.article_filename = os.path.join(self.directory_name, 'article.json')
		self.article_data = {}

		self.history_filename = os.path.join(self.directory_name, 'history.json')
		self.history_data = []

		self.open_json(search)

		if convert:
			self.convert_markdown()
		
		if history:
			self.view_history()

	def save(self):
		now = datetime.datetime.utcnow().isoformat()
		if not self.existence:
			self.article_data = {
				'edition' : 0,
				'created' : now,
				'last_updated' : now
			}
			self.existence = True
			if not os.path.isdir(self.directory_name):
				os.makedirs(self.directory_name)
		self.article_data['edition'] += 1

		self.history_data.append({
			'edition' : self.article_data['edition'],
			'editor' : flask.request.environ['REMOTE_ADDR'],
			'date' : now
		})

		md_filename = os.path.join(self.directory_name, "%d.md"%self.article_data['edition'])
		md_file = open(md_filename, 'w', encoding = 'utf-8')
		md_file.write(self.raw_data)
		md_file.close()

		article_file = open(self.article_filename, 'w', encoding = 'utf-8')
		json.dump(self.article_data, article_file, indent = '\t')

		history_file = open(self.history_filename, 'w', encoding = 'utf-8')
		json.dump(self.history_data, history_file, indent = '\t')

	def open_json(self, search):
		if os.path.isfile(self.article_filename):
			article_file = open(self.article_filename, 'r', encoding = 'utf-8')
			self.article_data = json.load(article_file)
			article_file.close()

			history_file = open(self.history_filename, 'r', encoding = 'utf-8')
			self.history_data = json.load(history_file)
			history_file.close()

			article_file = open(self.article_filename, 'w', encoding = 'utf-8')

			edition = self.article_data['edition']
			for i in range(edition, -1, -1):
				edition = i
				md_filename = os.path.join(self.directory_name, "%d.md"%i)
				self.existence = True
				if os.path.isfile(md_filename):
					if not search:
						md_file = open(md_filename, 'r', encoding = 'utf-8')
						self.raw_data = md_file.read()
						md_file.close()
					break
			self.article_data['edition'] = edition
			json.dump(self.article_data, article_file, indent = '\t')

	def convert_markdown(self):
		self.data = markdown.markdown(
			self.raw_data,
			output_format = 'html5',
			extensions = [
				WikiLinkPlusExtension(
					end_url = ''
				),
				FencedCodeExtension(
					lang_prefix = ''
				),
				TocPlusExtension(
					title = 'Table of Contents',
					slugify = do_nothing
				),
				DokiTableExtension(),
				'legacy_em', 'sane_lists', 'fenced_code'
			]
		)
	
	def view_history(self):
		self.history_out = ""
		for i in self.history_data:
			self.history_out += ("edition : %d"%i['edition'] + "<br/>editor : " + i['editor'] + "<br/>date : " + i['date'] + "<br/><br/>")

settings = Setting()
language = settings.get_language()

@application.route('/view/<path:title>')
def view(title):
	article = Article(title, convert = True)
	out = flask.render_template('view.html', settings = settings, language = language, article = article, title = title)
	return out

@application.route('/edit/<path:title>')
def edit(title):
	article = Article(title)
	title = (language['edit.title'] if article.existence else language['edit.title.create'])%title
	out = flask.render_template('edit.html', settings = settings, language = language, article = article, title = title)
	return out

@application.route('/edit-save/<path:title>', methods = ['POST'])
def edit_save(title):
	article = Article(title)
	text:str = flask.request.form['text']
	text = text.replace('\r', '')
	text = text.strip()
	if text != article.raw_data:
		article.raw_data = text
		article.save()
	return flask.redirect('/view/%s'%title)

@application.route('/history/<path:title>')
def history(title):
	article = Article(title, history = True)
	title = language['history.title']%title
	out = flask.render_template('history.html', settings = settings, language = language, article = article, title = title)
	return out

@application.route('/search/<path:text>')
def search(text):
	return text + "를 검색했습니다."

@application.route('/search/')
def search_none():
	return "검색한 내용 없음"

@application.route('/search-go/', methods = ['GET'])
def search_go():
	title = flask.request.args.get('search')
	filename = os.path.join(base_dir, 'articles', title, "article.json")
	if os.path.isfile(filename):
		file = open(filename, 'r', encoding = 'utf-8')
		article = json.load(file)
		filename = os.path.join(base_dir, 'articles', "%s"%title, "%d.md"%article['edition'])
		file.close()
		if os.path.isfile(filename):
			return flask.redirect('/view/%s'%title)
	return flask.redirect('/search/%s'%title)

@application.route("/")
def index():
	name = settings.mainpage
	return flask.redirect('/view/%s'%name)

if __name__ == '__main__':
	application.run(host = '0.0.0.0', port = 80)

