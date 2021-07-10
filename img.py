#! /usr/bin/env python3

import base64
import botconfig
import datetime
import math
import os
import sqldb
import tg
import time

def csprng(checkdup=lambda x: True,maxtrial=5):
    '''Generate a random number in base64 that checkdup returns True'''
    for trial in range(maxtrial):
        r = base64.b64encode(os.urandom(15),b'-_')
        if checkdup(r):
            return r
    return False

def csprc(i):
    '''Generate a random choice'''
    if i in (0,1):
        return 0
    t = math.ceil(math.log2(i))
    while True:
        k = 0
        for l in range(1+(t>>3)):
            k = (k<<8) + os.urandom(1)[0]
        k &= (1<<t+1)-1
        if k < i:
            return k

def canSpeak(api,gid):
    try:
        tmp = api.query('getChatMember',{'chat_id':gid,'user_id':api.info['id']},retry=0)
        return tmp['status'] in ('creator','administrator','member') or (tmp['status'] == 'restricted' and 'can_send_messages' in tmp and tmp['can_send_messages'])
    except tg.APIError:
        return False

def processItem(item,db,api):
    cmdList = ['/ping','/imginfo','/add','/'+botconfig.stickerName]+['/'+i for i in botconfig.stickerFlag]
    if 'message' in item:
        if 'text' in item['message'] and len(item['message']['text']) > 1 and item['message']['text'][0] == '/':
            hasToReply = False
            stripText = item['message']['text'].split('\n',1)[0].split(' ',1)[0]
            if len(stripText) > len(api.info['username']) and stripText[-len(api.info['username'])-1:] == '@'+api.info['username']:
                hasToReply = True
                stripText = stripText[:-len(api.info['username'])-1]
            stripText = stripText.lower()
            if stripText in cmdList:
                ## Start processing commands
                if stripText == '/ping':
                    api.sendMessage(item['message']['chat']['id'],'Hell o\'world! It took me '+str(time.time()-item['message']['date'])[:9]+' seconds to receive your message. Current thread count: '+str(api.clearFork()),{'reply_to_message_id':item['message']['message_id']})
                elif stripText == '/imginfo':
                    if 'reply_to_message' in item['message'] and ('sticker' in item['message']['reply_to_message'] or 'photo' in item['message']['reply_to_message']):
                        t = 'System Error'
                        if 'sticker' in item['message']['reply_to_message']:
#                        t = json.dumps(message['message']['reply_to_message']['sticker'])
                            t = 'Set name: '+item['message']['reply_to_message']['sticker']['set_name'] if 'set_name' in item['message']['reply_to_message']['sticker'] else 'Not found'
                            t += '\nFile ID: <code>'+item['message']['reply_to_message']['sticker']['file_id']
                            t += '</code>\nUnique ID: <code>'+item['message']['reply_to_message']['sticker']['file_unique_id']+'</code>'
                        elif 'photo' in item['message']['reply_to_message']:
#                        t = json.dumps(message['message']['reply_to_message']['photo'][0])
                            t = 'File ID: <code>'+item['message']['reply_to_message']['photo'][0]['file_id']
                            t += '</code>\nUnique ID: <code>'+item['message']['reply_to_message']['photo'][0]['file_unique_id']+'</code>'
                        api.sendMessage(item['message']['chat']['id'],'Here are the image info...\n'+t,{'reply_to_message_id':item['message']['message_id']})
                    else:
                        api.sendMessage(item['message']['chat']['id'],'Usage: reply to the image/sticker with /imginfo command.',{'reply_to_message_id':item['message']['message_id']})
                elif stripText == '/add':
                    if item['message']['from']['id'] not in botconfig.superAdmin:
                        api.sendMessage(item['message']['chat']['id'],'抱歉，只有超級管理員才可以給我添加其他圖片。')
                    elif 'reply_to_message' in item['message'] and ('sticker' in item['message']['reply_to_message'] or 'photo' in item['message']['reply_to_message'] or 'animation' in item['message']['reply_to_message']):
                        sf = '|'.join(item['message']['text'].split('\n',1)[0].split(' ')[1:])
                        if 'sticker' in item['message']['reply_to_message']:
                            db['main'].addItem((str(len(db['main'])),str(int(time.time())),str(item['message']['from']['id']),'sticker',item['message']['reply_to_message']['sticker']['file_id'],item['message']['reply_to_message']['sticker']['file_unique_id'],sf))
                        elif 'photo' in item['message']['reply_to_message']:
                            db['main'].addItem((str(len(db['main'])),str(int(time.time())),str(item['message']['from']['id']),'photo',item['message']['reply_to_message']['photo'][0]['file_id'],item['message']['reply_to_message']['photo'][0]['file_unique_id'],sf))
                        elif 'animation' in item['message']['reply_to_message']:
                            db['main'].addItem((str(len(db['main'])),str(int(time.time())),str(item['message']['from']['id']),'animation',item['message']['reply_to_message']['animation']['file_id'],item['message']['reply_to_message']['animation']['file_unique_id'],sf))
                        api.sendMessage(item['message']['chat']['id'],'該圖片已成功加入套餐。',{'reply_to_message_id':item['message']['reply_to_message']['message_id']})
                    else:
                        api.sendMessage(item['message']['chat']['id'],'Usage: reply to the image/sticker with /add command followed by all flags applicable to this sticker.',{'reply_to_message_id':item['message']['message_id']})
                elif stripText in ['/'+botconfig.stickerName]+['/'+i for i in botconfig.stickerFlag]:
                    pid = csprc(len(db['main']))
                    if stripText in ['/'+i for i in botconfig.stickerFlag]:
                        while stripText[1:] not in db['main'].getItem(str(pid),'flag').split('|'):
                            pid = csprc(len(db['main']))
                    ftype = db['main'].getItem(str(pid),'type')
                    if ftype == 'photo':
                        api.query('sendPhoto',{'chat_id':item['message']['chat']['id'],'photo':db['main'].getItem(str(pid),'fileid'),'reply_to_message_id':item['message']['message_id']})
                    elif ftype == 'sticker':
                        api.query('sendSticker',{'chat_id':item['message']['chat']['id'],'sticker':db['main'].getItem(str(pid),'fileid'),'reply_to_message_id':item['message']['message_id']})
                    elif ftype == 'animation':
                        api.query('sendAnimation',{'chat_id':item['message']['chat']['id'],'animation':db['main'].getItem(str(pid),'fileid'),'reply_to_message_id':item['message']['message_id']})
                    else:
                        print('Unsupported file type encountered.',db['main'][str(pid)])
                else:
                    api.sendMessage(item['message']['chat']['id'],'我本來應該有這功能的，但是好像主人偷懶沒做⋯⋯',{'reply_to_message_id':item['message']['message_id']})
                ## End processing commands
            elif hasToReply:
                api.sendMessage(item['message']['chat']['id'],'請問您對我有什麼奇怪的期待嗎？',{'reply_to_message_id':item['message']['message_id']})
    elif 'inline_query' in item:
        k = []
        for i in 'AB':
            pid = csprc(len(db['main']))
            if item['inline_query']['query'] in botconfig.stickerFlag:
                while item['inline_query']['query'] not in db['main'].getItem(str(pid),'flag').split('|'):
                    pid = csprc(len(db['main']))
            ftype = db['main'].getItem(str(pid),'type')
            if ftype == 'sticker':
                k.append({'type':'sticker','id':item['inline_query']['id']+i+'S','cache_time':1,'is_personal':True,'next_offset':'N','sticker_file_id':db['main'].getItem(str(pid),'fileid')})
            elif ftype == 'photo':
                k.append({'type':'photo','id':item['inline_query']['id']+i+'P','cache_time':1,'is_personal':True,'next_offset':'N','photo_file_id':db['main'].getItem(str(pid),'fileid')})
        api.query('answerInlineQuery',{'inline_query_id':item['inline_query']['id'],'results':k})

def run(db,api):
    batch = api.query('getUpdates')
    lastID = int(db['config'].getItem('lastid','value'))
    for item in batch:
        if item['update_id'] > lastID:
            db['config'].addItem(('lastid',str(item['update_id'])))
            try:
                processItem(item,db,api)
            except tg.APIError as e:
                if 'message' in item and not canSpeak(api,item['message']['chat']['id']):
                    print('Chat '+str(item['message']['chat']['id'])+' has blocked me. Quitting...')
                    try:
                        api.query('leaveChat',{'chat_id':item['message']['chat']['id']})
                    except tg.APIError:
                        pass
                print('Error processing the following item:')
                print(item)
            lastID = item['update_id']
        else:
            print('Message '+str(item['update_id'])+' skipped')
    while True:
        batch = api.query('getUpdates',{'offset':lastID+1,'timeout':20}) if lastID is not None else api.query("getUpdates",{'timeout':20})
        for item in batch:
            db['config'].addItem(('lastid',str(item['update_id'])))
            processItem(item,db,api)
            lastID = item['update_id']
        api.clearFork()
        time.sleep(1)

def main():
    dbFile = botconfig.db
    apiKey = botconfig.apiKey
    db = {'config':sqldb.sqliteDB(dbFile,'config')}
    if db['config'].getItem('dbver','value') != '1.1':
        raise tg.APIError('DB','DB Version Mismatch')
    db['main'] = sqldb.sqliteDB(dbFile,'main')
    api = tg.tgapi(apiKey)
    run(db,api)

if __name__ == '__main__':
    main()
