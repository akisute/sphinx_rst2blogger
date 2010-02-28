#!/usr/bin/env python
#coding:utf-8

from builder import BloggerBuilder


def setup(app):
    app.add_builder(BloggerBuilder)

