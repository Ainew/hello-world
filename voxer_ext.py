import sys
import os
import time
import requests
import threading
import shutil
import json
from urllib import request
from urllib import parse
from bs4 import BeautifulSoup
from splinter.browser import Browser



url = 'https://web.voxer.com'


current_dir = os.getcwd()
run = os.path.join(current_dir, 'run')
jsn = os.path.join(run, 'Json')
log = os.path.join(run, 'Log')
pic = os.path.join(run, 'Pic')
src = os.path.join(run, 'Src')
media = os.path.join(run, 'Media')
failed = os.path.join(run, 'Failed')
keypeople = os.path.join(run, 'Keypeople')




def WriteLog(content):
    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    file_name = os.path.join(log, current_date) + '.log'
    log_fd = open(file_name, 'a')
    content = current_time + '\t\t' + str(content) + '\n'
    log_fd.write(content)
    log_fd.close()

def WriteFailed(content):
    current_date = time.strftime('%Y-%m-%d',time.localtime(time.time()))
    file_name = os.path.join(failed, current_date) + '_failed.txt'
    log_fd = open(file_name, 'a')
    log_fd.write(content)
    log_fd.close()

def GetMediaFromJson(filename, cook, username):
    data_server = ''
    rlt = ''
    try:
        with open(filename, 'rb') as f:
            rlt = f.read()
            f.close()
            rlt = str(rlt)
            npos = rlt.find('https://prod')
            if npos != -1:
                nend = rlt.find('/', npos + 8)
                if nend != -1:
                    data_server = rlt[npos:nend + 1]
            else:
                return ''

        media_url = ''
        medirfrt = '%sget_body?&message_id=%s&format=%s&download=%s.%s'
        medir_type = ''
        with open(filename, 'rb') as f:
            rlt = f.readline()
            while rlt != b'':
                content = str(rlt)
                if content.find('"content_type":"image"') != -1:
                    medir_type = 'jpg'
                elif content.find('"content_type":"audio"') != -1:
                    medir_type = 'mp3'
                else:
                    rlt = f.readline()
                    continue
                npos = content.find('"message_id":"')
                nend = content.find('"', npos + 15)
                message_id = content[npos + 14:nend]
                media_url = medirfrt % (data_server, message_id, medir_type, message_id, medir_type)
                print(media_url)
                # save
                try:
                    response = requests.request('get', media_url, cookies=cook, timeout=30)
                    print(response)
                    if response.status_code != 200:
                        WriteLog(username + ' : ' + message_id + ' ' + str(response.status_code))
                        rlt = f.readline()
                        continue
                    content = response.content
                    with open(os.path.join(media, message_id) + '.' + medir_type, 'wb') as fd:
                         fd.write(content)
                    if flag:
                        output_dir = os.path.join(keypeople, username)
                        with open(os.path.join(output_dir, message_id) + '.' + medir_type, 'wb') as f:
                            f.write(content)
                            f.close()
                    time.sleep(5)
                except Exception as e:
                    print(1, e)
                rlt = f.readline()

    except Exception as e:
        print(2, e)

def GetPicFromJson(content, username):
    if content.find('"from":') == -1:
        WriteLog('NOT FOUND PIC FILE: ' + user)
        return
    nbegin = content.find('"from":"') + len('"from":"')
    nend = content.find('"', nbegin)
    uuid = content[nbegin:nend]
    url = "https://www.voxer.com/profile/" + uuid + '.jpg'
    res = requests.get(url=url, timeout=8)
    with open(os.path.join(pic, uuid) + ".jpg", 'wb') as f:
        f.write(res.content)
        f.close()
    if flag:
        output_dir = os.path.join(keypeople, username)
        if os.path.exists(output_dir) == False:
            os.mkdir(output_dir)
        with open(os.path.join(output_dir, username) + ".jpg", 'wb') as f:
            f.write(res.content)
            f.close()

def GetJson(username, json_dir, cook):
    for i in os.listdir(json_dir):
        with open(json_dir + i, 'rb') as f:
            try:
                rlt = f.readline()
                rlt = str(rlt)
                if rlt.find('{"op":"put_message",') != -1:
                    GetPicFromJson(rlt, username)
                    shutil.copy(json_dir + i, os.path.join(jsn, username) + ".json")
                    print()
                    WriteLog("Get Json Succeed.")
                    f.close()
                    t = threading.Thread(target=GetMediaFromJson, args=(json_dir + i, cook, username,))
                    t.start()
                    while t.is_alive():
                        time.sleep(2)
                    break
            except Exception as e:
                f.close()
                print("E ", e)
    time.sleep(2)

def Login(username, password):
    browser = Browser()
    # Find cache direction
    browser.visit('about:cache')
    json_dir = browser.html
    json_dir = json_dir.split('<th>Storage disk location:</th>')[2].split('</td>')[0].split('<td>')[1].replace(' ', '') + "\\entries\\"
    print(json_dir)
    # Login
    time.sleep(2)
    browser.visit(url)
    print('Trying Login...')
    time.sleep(8)
    browser.fill('user', username)
    browser.fill('pass', password)
    url1 = browser.url
    print(browser.url)
    try:
        browser.find_by_id('loginButton').click()
    except Exception as e:
        WriteLog(e)

    browser.forward()
    times = 0
    while True:
        time.sleep(10)
        if  len(browser.url) > 30:
            break
        times += 1
        if times < 4:
            info = 'The email or password you entered is incorrect'
            if browser.is_text_present(info):
                WriteLog(info + '  [' + username + '----' + password + ']')
                WriteFailed(username + '\t' + password + '\n')
                browser.quit()
                return
            if times == 3:
                print('Login timeout')
                WriteLog('Login timeout: ' + '[' + username + '----' + password + ']')
                browser.quit()
                return
        print('.\t')


    WriteLog('[' + username + '] login succeed!')
    print('succeed! Get Json...')
    time.sleep(45)
    cook = browser.cookies.all()
    GetJson(username, json_dir, cook)
    browser.quit()

def CheckConfigure():
    if os.path.exists('./voxer.conf') == False:
        return False
    if os.path.exists('./run') == False:
        os.mkdir(run)
        os.mkdir(jsn)
        os.mkdir(pic)
        os.mkdir(src)
        os.mkdir(log)
        os.mkdir(media)
        os.mkdir(failed)
        os.mkdir(keypeople)

    return True

def main():
    for name in os.listdir(src):
        print('Loading file [%s] '% name)
        with open(os.path.join(src, name), 'r') as fd:
            all_id = fd.read()
            id_list = all_id.split('\n')
            for a_id in id_list:
                print(a_id)
                result = a_id.split('\t')
                if len(result) == 3:
                    flag = True

                Login(result[0], result[1])

        os.remove(os.path.join(src, name))


if __name__ == '__main__':
    flag = False
    if CheckConfigure():
        while True:
            try:
                main()
            except Exception as e:
                print(e)
                flag = False
            time.sleep(30)
    else:
        print('NOT FIND CONF FILE.')