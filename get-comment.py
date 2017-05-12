# -*- coding:utf-8 -*-
#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup
import time
import os
import json
import sqlite3
import re
import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud,STOPWORDS,ImageColorGenerator
from scipy.misc import imread  
from urllib import unquote

reload(sys)
sys.setdefaultencoding('utf-8')   
requests.adapters.DEFAULT_RETRIES = 5 

'''
https://itunes.apple.com/cn/rss/newapplications/limit=100/xml
https://itunes.apple.com/cn/rss/newfreeapplications/limit=100/xml
https://itunes.apple.com/cn/rss/newpaidapplications/limit=100/xml
https://itunes.apple.com/cn/rss/topfreeapplications/limit=100/xml
https://itunes.apple.com/cn/rss/topfreeipadapplications/limit=100/xml
https://itunes.apple.com/cn/rss/topgrossingapplications/limit=100/xml
https://itunes.apple.com/cn/rss/topgrossingipadapplications/limit=100/xml
https://itunes.apple.com/cn/rss/toppaidapplications/limit=100/xml
https://itunes.apple.com/cn/rss/toppaidipadapplications/limit=100/xml
https://itunes.apple.com/cn/rss/toppaidipadapplications/limit=100/genre=6018/xml  Books   
155.3
business 6000
catalogs 6022
education 6017
entertainment 6016
finance 6015
food & drink 6023
games 6014
health & fitness 6013
lifestyle 6012
medical 6020
music 6011
navigation 6010
news 6009 
newsstand 6021
...
https://rss.itunes.apple.com/us/?urlDesc=


https://itunes.apple.com/lookup?id=
https://itunes.apple.com/rss/customerreviews/id=876336838/json
https://itunes.apple.com/cn/rss/customerreviews/page=1/id=490655927/sortby=mostrecent/json
https://itunes.apple.com/rss/customerreviews/page=1/id=414478124/sortby=mostrecent/json?l=en&&cc=cn
'''

def do_jieba(appid):

	text = ''
	conn = sqlite3.connect('appstore.sqlite3')
	conn.row_factory = sqlite3.Row
	sql = 'select content from comments where appid="%s"'%(appid)
	rows = conn.cursor().execute(sql).fetchall()

	for row in rows:
		text += ' '.join(jieba.cut(row[0], cut_all=True))

	'''
	读取模块 
	'''
	fout = open('jieba_txt/%s.txt'%(appid),'a')
	fout.write(text)
	fout.close()

def do_wordcloud(appid):

	sfile = open('jieba_txt/%s.txt'%(appid),'r')
	text = sfile.read().decode('utf-8')
	
	bg_img = imread('apple.png')
	
	wc_with_logo = WordCloud(
		background_color = 'white',    # 设置背景颜色
    	mask = bg_img,        # 设置背景图片
    	max_words = 2000,            # 设置最大现实的字数
    	stopwords = STOPWORDS,        # 设置停用词
    	font_path = '/Library/Fonts/Arial Unicode.ttf',# 设置字体格式，如不设置显示不了中文
    	max_font_size = 50,            # 设置字体最大值
    	random_state = 30,            # 设置有多少种随机生成状态，即有多少种配色方案
                	)

	wc = WordCloud(
		background_color = 'white',    # 设置背景颜色
    	max_words = 2000,            # 设置最大现实的字数
    	stopwords = STOPWORDS,        # 设置停用词
    	font_path = '/Library/Fonts/Arial Unicode.ttf',# 设置字体格式，如不设置显示不了中文
    	max_font_size = 50,            # 设置字体最大值
    	random_state = 30,            # 设置有多少种随机生成状态，即有多少种配色方案

    	)

	wc.generate(text)
	wc_with_logo.generate(text)
	#image_colors = ImageColorGenerator(backgroud_Image)
	#wc.recolor(color_func = image_colors)
	# plt.imshow(wc)
	# plt.axis('off')
	# plt.show()
	wc.to_file('word_cloud_img/%s.jpg'%(appid))
	wc_with_logo.to_file('word_cloud_img/%s_with_logo.jpg'%(appid))


def create_or_open_db():
    conn = sqlite3.connect('appstore.sqlite3')
    cur = conn.cursor()
    cur.execute("CREATE TABLE if not exists app_info(id integer PRIMARY KEY autoincrement , appid text ,app_name text ,bundle_id text ,app_detail text null ,url text)")
    cur.execute("CREATE TABLE if not exists comments(id integer PRIMARY KEY, appid text , app_name text, rating real, title text , content text )")
    return conn , cur

def sqlite_insert(conn, table, row):

    cols = ', '.join('"{}"'.format(col) for col in row.keys())
    vals = ', '.join(':{}'.format(col) for col in row.keys())
    sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(table, cols, vals)
    conn.cursor().execute(sql, row)
    conn.commit()

def get_all_comments_by_api(appid): #todo 

	api = 'https://itunes.apple.com/WebObjects/MZStore.woa/wa/userReviewsRow?id='+str(appid)+'&displayable-kind=11&startIndex=0&endIndex=100&sort=1&appVersion=current'
	cookies = ''
	print api

def get_comments_by_api(appid):
	continue_flag = 1
	#us
	#api = 'https://itunes.apple.com/rss/customerreviews/page=1/id=' + str(appid) + '/sortby=mostrecent/json'

	api = 'https://itunes.apple.com/cn/rss/customerreviews/page=1/id=' + str(appid) + '/sortby=mostrecent/json'
	response = requests.get(api)
	d = json.loads(response.content)
	
	try:
		name = d['feed']['entry'][0]['im:name']['label']
	except:
		print 'no comments'
		continue_flag = 0
		return continue_flag 
	print name
	
	
	for i in range(1,2):
		page = i
		# us
		api = 'https://itunes.apple.com/rss/customerreviews/page='+str(page)+'/id=' + str(appid) + '/sortby=mostrecent/json'
		print api
		# cn
		api = 'https://itunes.apple.com/cn/rss/customerreviews/page='+str(page)+'/id=' + str(appid) + '/sortby=mostrecent/json'
		response = requests.get(api)
		d = json.loads(response.content)
		time.sleep(2)
		
		print '第%s页'%(i)
		for j in range(1,100):
			try:

				title = d['feed']['entry'][j]['title']['label']
				#print title
				comment = d['feed']['entry'][j]['content']['label']
				rating = d['feed']['entry'][j]['im:rating']['label']
				# id integer PRIMARY KEY, appid text , app_name text, rating real, title text , content text )
				conn = sqlite3.connect('appstore.sqlite3')
				conn.text_factory = str
				print title
				sqlite_insert(conn, 'comments', {
					'appid': appid ,
					'app_name': 'N/A' ,
					'rating':rating ,
					'title':title,
					'content':comment
					
					})
				conn.commit()
				conn.close()
			except Exception,e:
				print str(e)
				break
		
	return continue_flag 

def rss_xml_analysis():

	print '输入xml名称without后缀'
	xml_name = raw_input()
	xfile = open('%s.xml'%(xml_name),'r').read()
	re_id_tag = re.compile(r'<id .+</id>')
	tag_list = re.findall(re_id_tag , xfile)
	
	for id_tag in tag_list:
		soup = BeautifulSoup(id_tag)
		appid =  soup.findAll('id')[0]['im:id']
		bundle_id = soup.findAll('id')[0]['im:bundleid']
		url = soup.findAll('id')[0].contents[0]
		re_url = re.compile(r'app/.+/id')
		app_name = re.findall(re_url , url)[0].rstrip('/id').lstrip('app/')
		app_name = unquote(str(app_name)).encode('utf-8')
		conn = sqlite3.connect('appstore.sqlite3')
		conn.text_factory = str
		sqlite_insert(conn, 'app_info', {
			'appid': appid,
			'bundle_id': bundle_id,
			'app_name':app_name,
			'url': url
			})

		
	conn.commit()
	conn.close()

#  appid text ,app_name text ,bundle_id text ,app_detail text ,url text
def sql_exp():
	conn , cur = create_or_open_db()
	sql =' INSERT INTO app_info VALUES (null,"24","appname","fsfs")'
	cur.execute(sql)
	conn.commit()
	conn.close()

def main():

	conn = sqlite3.connect('appstore.sqlite3')
	conn.row_factory = sqlite3.Row
	sql = 'select appid from app_info'
	rows = conn.cursor().execute(sql).fetchall()

	for row in rows:
		print '正在获取id%s'%(row[0])
		didfile = open('did.txt','r+a')
		didflag = 0
		for line in didfile.readlines():
			if row[0].strip() == line.strip():
				print 'already did that ! skip it.'
				didflag = 1
				break
		if didflag == 0:
			is_continue = get_comments_by_api(row[0])
			if is_continue == 1:
				try:
					do_jieba(row[0])
					do_wordcloud(row[0])
				except:
					print 'do not enough comments for analysis!!!'
			didfile.write(row[0])	
			didfile.write('\n')	
			didfile.close()		
			

	
if __name__ == '__main__':

	print '选择rss导入db自行修改注释'

	create_or_open_db() #create or open 

	#rss_xml_analysis() # save as sqlite

	main()