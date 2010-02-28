#!/usr/bin/env python
#coding:utf-8
from sphinx.builders.text import TextBuilder
from writer import BloggerWriter


class BloggerBuilder(TextBuilder):
    name = 'blogger'
    format = 'blogger'
    out_suffix = '.txt'

    def prepare_writing(self, docnames):
        self.writer = BloggerWriter(self)

