# coding=utf-8
import json
import os
import sqlite3

import brotli
import requests

from bot_prcdCampaignCategory import parse_campaign

datadir = os.path.join(os.path.dirname(__file__), 'data')
distdir = os.path.join(os.path.dirname(__file__), 'dist')
if not os.path.exists(datadir):
    os.makedirs(datadir)
if not os.path.exists(distdir):
    os.makedirs(distdir)


def update(name, verurl, dburl):
    localver = os.path.join(datadir, os.path.basename(verurl))
    localdb = os.path.join(datadir, name+'.sqlite')
    if os.path.exists(localver):
        with open(localver, 'r', encoding='utf-8') as lv:
            lvj = json.load(lv)
            localversion = int(lvj.get('TruthVersion', 0))
    else:
        localversion = 0
        print('local-cache database not found')
    rmver_res = requests.get(verurl)
    if rmver_res.status_code != 200:
        print(f'bad response from url {rmver_res.status_code}: {verurl}')
        return 0
    rmver = int(rmver_res.json().get('TruthVersion', 0))
    if rmver <= localversion:
        print('local-cache database is up-to-date')
        return 0
    with open(localver, 'w') as lv:
        lv.write(rmver_res.text)
    rmdb_res = requests.get(dburl)
    if rmdb_res.status_code != 200:
        print(f'bad response from url {rmdb_res.status_code}: {dburl}')
        return 0
    rmdb = brotli.decompress(rmdb_res.content)
    with open(localdb, 'wb') as ld:
        ld.write(rmdb)
    data = []
    with sqlite3.connect(localdb) as con:
        for row in con.execute("""
            SELECT start_time, end_time
            FROM clan_battle_period
        """):
            data.append({
                'name': '公会战',
                'start_time': row[0],
                'end_time': row[1],
            })
        for row in con.execute("""
            SELECT start_time, end_time
            FROM campaign_freegacha
        """):
            data.append({
                'name': '免费十连',
                'start_time': row[0],
                'end_time': row[1],
            })
        for row in con.execute("""
            SELECT campaign_category, value, start_time, end_time
            FROM campaign_schedule
        """):
            campaign_name = parse_campaign(row[0])
            if campaign_name is None:
                continue
            data.append({
                'name': campaign_name+str(row[1]/1000)+'倍',
                'start_time': row[2],
                'end_time': row[3],
            })
        for row in con.execute("""
            SELECT start_time, end_time
            FROM tower_schedule
        """):
            data.append({
                'name': '露娜塔',
                'start_time': row[0],
                'end_time': row[1],
            })
        for row in con.execute("""
            SELECT a.start_time, a.end_time, b.title
            FROM hatsune_schedule AS a JOIN event_story_data AS b ON a.event_id = b.value
        """):
            data.append({
                'name': '活动：' + row[2],
                'start_time': row[0],
                'end_time': row[1],
            })
    with open(os.path.join(distdir, name+'.json'), 'w') as j:
        json.dump(data, j, ensure_ascii=True, separators=(',', ':'))
        print('update success')
    return 1

new_items = 0

print('updating database (cn)')
try:
    new_items += update(
        'cn',
        'https://redive.estertion.win/last_version_cn.json',
        'https://redive.estertion.win/db/redive_cn.db.br',
    )
except Exception as e:
    print(e)

print('updating database (jp)')
try:
    new_items += update(
        'jp',
        'https://redive.estertion.win/last_version_jp.json',
        'https://redive.estertion.win/db/redive_jp.db.br',
    )
except Exception as e:
    print(e)

print('updating database (tw)')
try:
    new_items += update(
        'tw',
        'https://kkbllt.github.io/json/lastver_tw.json',
        'https://kkbllt.github.io/br/redive_tw.db.br',
    )
except Exception as e:
    print(e)

print(f'updating finished, {new_items} new items found')
print(f'::set-output name=new_items::{new_items}')
