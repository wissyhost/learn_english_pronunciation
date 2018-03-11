import json
import os
import urllib.parse

import requests
import time

import execjs

# apt/yum install mpg123 or apt/yum install mpg321
# pip install requests
# pip install PyExecJS

def get_js():
    """
    加载JS文件
    :return: js 字符串
    """
    f = open("./sign.js", 'r', encoding='UTF-8')
    line = f.readline()
    htmlstr = ''
    while line:
        htmlstr = htmlstr + line
        line = f.readline()
    return htmlstr

def get_word_mp3(words,zh_words, name):
    """
    获取 英文发音(百度)，英文发音(EF)，中文发音(百度)
    :param words: 单词
    :param zh_words: 中文翻译
    :param name: 保存的文件名称
    :return: 3个文件的名称
    """
    zh_name=name.replace(".", "_zh.")
    en_name=name.replace(".", "_en.")
    ef_name=name.replace(".", "_ef.")
    if not os.path.exists(en_name):
        respon = requests.get("http://fanyi.baidu.com/gettts?lan=en&text=%s&spd=3&source=web" % words)
        with open(en_name, 'wb') as f:
            f.write(respon.content)
    if not os.path.exists(zh_name):
        respon = requests.get("http://fanyi.baidu.com/gettts?lan=zh&text=%s&spd=3&source=web" % urllib.parse.unquote(zh_words))
        with open(zh_name, 'wb') as f:
            f.write(respon.content)
    if not os.path.exists(ef_name):
        if len(words)>2:
            respon = requests.get("https://cns.ef-cdn.com/etownresources/dictionary_mp3/Headword/US/%s/%s/%s/%s_us_1.Mp3"% (words[0],words[0:2],words[0:3],words))
        else:
            respon = requests.get("https://cns.ef-cdn.com/etownresources/dictionary_mp3/Headword/US/%s/%s/%s_/%s_us_1.Mp3"% (words[0],words[0:2],words[0:2],words))
        with open(ef_name, 'wb') as f:
            f.write(respon.content)

    return zh_name,en_name,ef_name

import subprocess

def play_mp3(words,zh_words):
    """
    使用linux系统内置的软件进行播放
    Windows 可以使用mp3play播放
    :param words: 单词
    :param zh_words: 中文翻译
    :return:
    """
    zh_name, en_name,ef_name=get_word_mp3(words,zh_words,"mp3/%s.mp3"%words)
    # subprocess.Popen(['mpg123', '-q', name.replace(".","_en.")]).wait()
    subprocess.Popen(['mpg123', '-q', zh_name]).wait()
    # 百度发音不太标准
    # time.sleep(0.4)
    # subprocess.Popen(['mpg123', '-q', en_name]).wait()
    time.sleep(0.4)
    subprocess.Popen(['mpg123', '-q', ef_name]).wait()
    # time.sleep(0.4)
    # subprocess.Popen(['mpg123', '-q', en_name]).wait()

def get_word_desc(word):
    """
    从百度接口获取单词详细描述 如：单词的翻译，单词的音标
    :param word:
    :return:
    """
    headers = {
        # 与下面的token是一对
        'Cookie': 'BAIDUID=A7013D3CA5B6E24BE246A20EC6428884:FG=1;',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    }
    jsstr = get_js()
    ctx = execjs.compile(jsstr)
    # print(ctx.call('hash', '320305.131321201', "今天天气怎么样"))
    data = {
        'from': 'en', 'to': 'zh', 'query': word, 'transtype': 'translang',
        'simple_means_flag': '3',
        # 签名 调用js实现
        'sign': ctx.call('hash', word,'320305.131321201'),
        # 用户唯一token 与header的Cookie是一对
        'token': '1d9ae22ffe27773505723fe275e363c7'

    }

    respon=requests.post('http://fanyi.baidu.com/v2transapi',headers=headers,data=data)
    # print(json.dumps(json.loads(respon.text.encode('utf-8')),ensure_ascii=False))
    dst=json.loads(respon.text.encode('utf-8'))['trans_result']['data'][0]['dst']
    src=json.loads(respon.text.encode('utf-8'))['trans_result']['data'][0]['src']
    try:
        ph_en=json.loads(respon.text.encode('utf-8'))['dict_result']['simple_means']['symbols'][0]['ph_en']
    except Exception as e:
        # 句子无法获取音标
        print("报错了")
        ph_en = None
    return dst,src,ph_en

with open("./words.txt") as f:
    for i in filter(lambda fil: not fil.startswith("--") and not fil.startswith("#"),map(lambda c:c.replace("\n",""),f.readlines())):
        dst,src,ph_en=get_word_desc(i)
        print(src,"/"+ph_en+"/",dst)
        play_mp3(src,dst)
