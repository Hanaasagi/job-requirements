# -*-coding:UTF-8 -*-

import sys
import urllib
import json
import time
import multiprocessing
import BeautifulSoup
from Queue import Empty

INTERFACE = ('http://www.lagou.com/jobs/positionAjax.json?'
             'px=default&yx=10k-15k&needAddtionalResult=false')
JOBDETAIL = 'http://www.lagou.com/jobs/{0}.html'


def get_page_data(task, queue, keyword):
    while True:
        try:
            page = task.get(timeout=1)
        except Empty:
            break
        post_data = {'kd': keyword, 'pn': page, 'first': 'false'}
        opener = urllib.urlopen(INTERFACE, urllib.urlencode(post_data))
        jsonData = json.loads(opener.read())
        results = jsonData['content']['positionResult']['result']
        for result in results:
            queue.put(result['positionId'])
    sys.exit()


def get_job_detail(queue, result):
    while True:
        try:
            positionId = queue.get(timeout=1)
        except Empty:
            print multiprocessing.current_process().name + 'exit'
            break
        url = JOBDETAIL.format(positionId)
        print url, multiprocessing.current_process().name
        opener = urllib.urlopen(url)
        html = opener.read()
        soup = BeautifulSoup.BeautifulSoup(html)
        content = soup.findAll(attrs={"class": "job_bt"})[0]
        result.put(
            '{0}\n{1}<hr/>'.format(JOBDETAIL.format(positionId), content))
    sys.exit()


def main(keyword):
    task = multiprocessing.Queue()
    queue = multiprocessing.Queue()
    result = multiprocessing.Manager().Queue()

    post_data = {'kd': keyword, 'pn': 1, 'first': 'true'}
    opener = urllib.urlopen(INTERFACE, urllib.urlencode(post_data))
    jsonData = json.loads(opener.read())

    # 页数
    total = jsonData['content']['positionResult']['totalCount']
    size = jsonData['content']['positionResult']['resultSize']
    pageNums = total / size
    if total % size:
        pageNums += 1
    results = jsonData['content']['positionResult']['result']
    for r in results:
        queue.put(r['positionId'])

    for i in range(2, pageNums + 1):
        task.put(i)

    num_consumers = multiprocessing.cpu_count()
    processes = [multiprocessing.Process(
        target=get_page_data, args=(task, queue, keyword))]
    for _ in range(num_consumers):
        processes.append(multiprocessing.Process(target=get_job_detail,
                                                 args=(queue, result)))
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    print 'processes over'

    print result.qsize()
    with open('jobs.html', 'w+') as f:
        f.write('<!DOCTYPE HTML>\n<html>\n<head>\n<meta charset="utf-8">\n'
                '</head>\n<body>\n')
        while not result.empty():
            a = result.get()
            f.write(a)
        f.write('\n</body>\n</html>')

if __name__ == '__main__':
    langs = ('python', 'java', 'ruby', 'go', 'php', 'Android', 'iOS')
    if len(sys.argv) < 2 or sys.argv[1] not in langs:
        print 'You should choose a languaga {}'.format(langs)
        sys.exit()
    start_time = time.time()
    main(sys.argv[1])
    print time.time() - start_time
