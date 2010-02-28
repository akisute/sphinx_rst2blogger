========================================================
Sphinx を用いて、 reST の文章を Blogger の原稿に変換する
========================================================

`BPStudy #30 <http://atnd.org/events/3015>`_ にてSphinx講座があったので、早速それを生かしてreSTでBlogger向けの原稿を作ってみることにします。

見出しのテスト
==============

Hello world!
foo bar
改行のテスト

段落のテスト

それではインラインマークアップのテストをしてみましょう。 *強調* 、 **強い強調** 、 ``code sample(): print sample`` 。いかがかな？

`リンクのテスト <http://akisute.com>`_ リンクの末尾には必ず_を付ける必要があります。

さらにもう一つ見出し
====================

* ul 1
* ul 2
* ul 3
  ul 3 continues

#. ol 1

   #. ol 1-1
   #. ol 1-2

#. ol 2
   ol 2 continues
   ol 2 continues again

#. ol 3

番号リストの後に普通のパラグラフを入れてみるとどうなるか

定義リスト
    定義リストをつくるにはインデントを頭に付ける

    なんか定義リストの作り方がおかしいって怒られた

どうすればいい？
    しらんがな
    どうするもこうするも

::

    /** This is the pre message*/
    def pre(self, message):
       print 'this is the pre message'

だいたいうまくいっているようです。 okay fine.

