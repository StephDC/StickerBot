#! /usr/bin/env python3

import sys
import sqldb

def update0(db):
    if db[0].getItem('dbver','value') != '1.0':
        raise TypeError("Wrong Database Version")
    db[1].data.execute("alter table 'main' add 'flag'")
    db[1].data.execute("update 'main' set flag = ''")
    db[1].data.execute("update 'main' set flag = 'flag' where header='header'")
    db[1].updateDB()
    db[0].addItem(['dbver','1.1'])
    print("DB version updated to 1.1")

def main(args):
    if len(args) == 0 or args[0] in ('-h','--help','-?'):
        print(sys.argv[0]+' - Update StickerBot DB')
        print('Synopsis:')
        print('\t'+sys.argv[0]+' init.db')
        exit()
    tmp = sqldb.sqliteDB(args[0],'config')
    db = [tmp,sqldb.sqliteDB(tmp,'main')]
    if db[0].getItem('dbver','value') == '1.0':
        update0(db)
    print("Your database is up-to-date.")

if __name__ == '__main__':
    main(sys.argv[1:])
