#!/usr/bin/env python
# -*- coding: utf-8 -*-
#http://segfault.in/2010/07/parsing-html-table-in-python-with-beautifulsoup/
#https://docs.python.org/2/howto/argparse.html

import urllib
import re
import time
import argparse
import os.path

from dateutil import parser as dateparser
from BeautifulSoup import BeautifulSoup

class Movie:
	def __init__(self):
		# nazev
		self.title = None
		# popis
		self.description = None
		# casy promitani
		self.times = []
		# vstup
		self.entrance = None
		# linky na rezervaci
		self.links = []

	def __str__(self):
		return (self.title + "\n" + self.description + "\n" + self.get_times_and_links_str() + "\n" + self.entrance).encode('utf-8')

	def get_times_str(self):
		times_str = ""
		for t in self.times:
			times_str += (t + "\n")
		return times_str[:-1]

	def get_times_and_links_str(self):
		times_and_links_str = ""
		for t, l in zip(self.times, self.links):
			times_and_links_str += (t + " -> " + l + "\n")
		return times_and_links_str[:-1]

class MovieParser:
	def __init__(self, args):
		self.RESERVATION_STRING = "REZERVACE - ONLINE"
	
	def parse(self, html):
		soup = BeautifulSoup(html)
		table = soup.find("table", id="program")
		rows = table.findAll("tr")

		content = 1
		# vysledny seznam
		movies = []
		movie = Movie()
		for r in rows:
			cols = r.findAll("td")
			for c in cols:
				times, links = [], []
				text = c.find(text=True)
				ptext = text.strip()
				# rezervace online -> casy
				if text == self.RESERVATION_STRING:
					a = c.findAll("a")
					for d in a:
						time = d.find(text=True)
						times.append(time[3:])
						links.append(d['href'])
					movie.times = times
					movie.links = links
				# zbytek, v poradi nazev, popis a vtupne
				elif ptext:
					# nazev
					if content == 1:
						movie.title = ptext
						content = 2
					# popis
					elif content == 2:
						movie.description = ptext
						content = 3
					# vstup
					elif content == 3:
						movie.entrance = ptext
						content = 1
						# ulozeni a novy film
						movies.append(movie)
						movie = Movie()
		return movies

class MovieHtmlProvider:
	def __init__(self, args):
		self.args = args
		self.filename = "/tmp/inobce.py.html"

	def get(self):
		html = None

		if self.args.use_cache and os.path.isfile(self.filename):
			with open(self.filename, "r") as myfile:
				html = myfile.read()
		else:
			f = urllib.urlopen("http://www.kinoboskovice.cz/bpProgram.aspx")
			html = f.read()

			with open(self.filename, "w") as myfile:
				myfile.write(html)
		
		return html

class MovieArgumentParser():
	def __init__(self):
		self.parser = argparse.ArgumentParser()
		self.parser.add_argument("-f", "--from_date", help="get movies from the this date")
		self.parser.add_argument("-t", "--to_date", help="get movies to the this date")
		self.parser.add_argument("-n", "--name", help="get movies by name")
		self.parser.add_argument("-uc", "--use_cache", action="store_true", help="use htmlimput from disk (default in /tmp/)")
		self.parser.add_argument("-so", "--short_output", action="store_true", help="show short output")
	
	def parse_args(self):
		return self.parser.parse_args()

class MovieFilter:
	def __init__(self, movies, args):
		self.result = []
		self.movies = movies
		self.args = args

	def mfilter(self):
		if self.args.name:
			self.__filter_by_name(self.args.name)
			self.movies = list(self.result)

		if self.args.from_date or self.args.to_date:
			self.__filter_by_date(self.args.from_date, self.args.to_date)
			self.movies = list(self.result)

		return self.movies

	def __filter_by_name(self, name):
		for movie in self.movies:
			if name.lower() in movie.title.lower():
				self.result.append(movie)
	
	def __filter_by_date(self, from_date=None, to_date=None):
		for movie in self.movies:
			isFrom = False
			isTo = False
			for time in movie.times:
				if not from_date or dateparser.parse(from_date) <= dateparser.parse(time):
					isFrom = True
					if isTo:
						break
				if not to_date or dateparser.parse(to_date) >= dateparser.parse(time):
					isTo = True
					if isFrom:
						break

			if isFrom and isTo:
				self.result.append(movie)

class MoviePrinter:
	def __init__(self, movies, args):
		self.movies = movies
		self.args = args

	def print_movies(self):
		if self.args.short_output:
			for m in self.movies:
				print m.title
				print m.get_times_str()
				print m.entrance
				print
		else:
			for m in self.movies:
				print m
				print

def Main():
	args = MovieArgumentParser().parse_args()
	html = MovieHtmlProvider(args).get()
	movies = MovieParser(args).parse(html)
	movies = MovieFilter(movies, args).mfilter()
	MoviePrinter(movies, args).print_movies()
	
if __name__ == "__main__":
	Main()

