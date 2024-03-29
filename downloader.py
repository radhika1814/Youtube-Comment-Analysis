#Python comment retrieval code:
#TEAM MEMBERS:
#(1) RADHIKA MITTAL
#(2) VRUSHALI KADAM

#!/usr/bin/env python

import sys
import time
importjson
import requests
importargparse
import lxml.html

fromlxml.cssselect import CSSSelector

YOUTUBE_COMMENTS_URL = 'https://www.youtube.com/all_comments?v={youtube_id}'
YOUTUBE_COMMENTS_AJAX_URL = 'https://www.youtube.com/comment_ajax'

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'


deffind_value(html, key, num_chars=2):
pos_begin = html.find(key) + len(key) + num_chars
pos_end = html.find('"', pos_begin)
return html[pos_begin: pos_end] 


defextract_comments(html):
tree = lxml.html.fromstring(html)
item_sel = CSSSelector('.comment-item')
text_sel = CSSSelector('.comment-text-content')
time_sel = CSSSelector('.time')
author_sel = CSSSelector('.user-name')

for item in item_sel(tree):
yield {'cid': item.get('data-cid'),
               'text': text_sel(item)[0].text_content(),
               'time': time_sel(item)[0].text_content().strip(),
               'author': author_sel(item)[0].text_content()}


defextract_reply_cids(html):
tree = lxml.html.fromstring(html)
sel = CSSSelector('.comment-replies-header > .load-comments')
return [i.get('data-cid') for i in sel(tree)]


defajax_request(session, url, params, data, retries=10, sleep=20):
for _ in range(retries):
response = session.post(url, params=params, data=data)
ifresponse.status_code == 200:
response_dict = json.loads(response.text)
returnresponse_dict.get('page_token', None), response_dict['html_content']
else:
time.sleep(sleep)


defdownload_comments(youtube_id, sleep=1):
session = requests.Session()
session.headers['User-Agent'] = USER_AGENT

    # Get Youtube page with initial comments
response = session.get(YOUTUBE_COMMENTS_URL.format(youtube_id=youtube_id))
html = response.text
reply_cids = extract_reply_cids(html)

ret_cids = []
for comment in extract_comments(html):
ret_cids.append(comment['cid'])
yield comment

page_token = find_value(html, 'data-token')
session_token = find_value(html, 'XSRF_TOKEN', 4)

first_iteration = True

    # Get remaining comments (the same as pressing the 'Show more' button)
whilepage_token:
data = {'video_id': youtube_id,
                'session_token': session_token}

params = {'action_load_comments': 1,
                  'order_by_time': True,
                  'filter': youtube_id}

iffirst_iteration:
params['order_menu'] = True
else:
data['page_token'] = page_token

response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL, params, data)
if not response:
break

page_token, html = response

reply_cids += extract_reply_cids(html)
for comment in extract_comments(html):
if comment['cid'] not in ret_cids:
ret_cids.append(comment['cid'])
yield comment

first_iteration = False
time.sleep(sleep)

    # Get replies (the same as pressing the 'View all X replies' link)
forcid in reply_cids:
data = {'comment_id': cid,
                'video_id': youtube_id,
                'can_reply': 1,
                'session_token': session_token}

params = {'action_load_replies': 1,
                  'order_by_time': True,
                  'filter': youtube_id,
                  'tab': 'inbox'}

response = ajax_request(session, YOUTUBE_COMMENTS_AJAX_URL, params, data)
if not response:
break

        _, html = response

for comment in extract_comments(html):
if comment['cid'] not in ret_cids:
ret_cids.append(comment['cid'])
yield comment
time.sleep(sleep)


def main(argv):
parser = argparse.ArgumentParser(add_help=False, description=('Download Youtube comments without using the Youtube API'))
parser.add_argument('--help', '-h', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
parser.add_argument('--youtubeid', '-y', help='ID of Youtube video for which to download the comments')
parser.add_argument('--output', '-o', help='Output filename (output format is line delimited JSON)')

try:
args = parser.parse_args(argv)

youtube_id = args.youtubeid
output = args.output

if not youtube_id or not output:
parser.print_usage()
raiseValueError('you need to specify a Youtube ID and an output filename')

print 'Downloading Youtube comments for video:', youtube_id
count = 0
with open(output, 'wb') as fp:
for comment in download_comments(youtube_id):
print>>fp, json.dumps(comment)
count += 1
sys.stdout.write('Downloaded %d comment(s)\r' % count)
sys.stdout.flush()
print '\nDone!'


except Exception, e:
print 'Error:', str(e)
sys.exit(1)


if __name__ == "__main__":
main(sys.argv[1:])
