import json
import os
import re
import shutil
import sys
import time
import tkinter
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from threading import Thread
from tkinter import filedialog, messagebox, ttk

import requests


class Mode(Enum):
    Normal = 'normal'
    Extract = 'extract'


class Tag(Enum):
    ClientOnly = 'client-only'
    ServerOnly = 'server-only'
    Optional = 'optional'


def ask_mods_path():
    result = filedialog.askdirectory()
    if result:
        mods_path.set(result)


def download(mod: dict) -> None:
    retry = 5
    for tries in range(retry):
        dir = '/'.join(mod['filename'].split('/')[:-1])
        if dir:
            dir += '/'
        filename = mod['filename'].split('/')[-1]
        print(f'[{filename}] ダウンロード中')
        try:
            url = mod['url']
            match = CURSEFORGE_PATTERN.match(url)
            if match:
                url = FORGE_CDN.format(match.group('id')[:4], match.group('id')[4:], filename)
            res = requests.get(url, stream=True)
            res.raise_for_status()
            with open(f'{dir}{filename}', 'wb') as f:
                res.raw.decode_content = True
                shutil.copyfileobj(res.raw, f)

            if mod['mode'] == Mode.Extract.value:
                print(f'[{filename}] 解凍中')
                with zipfile.ZipFile(f'{dir}{filename}', 'r') as f:
                    f.extractall(dir)
                os.remove(f'{dir}{filename}')
            print(f'[{filename}] ダウンロード完了')
        except requests.exceptions.MissingSchema:
            print(f'[{filename}] URLが無効です: {url}', file=sys.stderr)
            traceback.print_exc()
            raise
        except Exception as e:
            if e.__class__ is requests.exceptions.HTTPError and res.status_code == 404:
                print(f'[{filename}] ファイルが見つかりません。正しいURL/ファイル名になっているか確認してください', file=sys.stderr)
                traceback.print_exc()
                raise

            if (tries + 1) < retry:
                print(f'[{filename}] ダウンロード失敗、5秒後に再試行します {tries + 1}/{retry}')
                traceback.print_exc()
            else:
                print(f'[{filename}] ダウンロード失敗')
                traceback.print_exc()
                raise
            time.sleep(5)
        else:
            break


def run():
    try:
        os.makedirs(mods_path.get(), exist_ok=True)
    except FileNotFoundError:
        print('正しいパスを指定してください', file=sys.stderr)
        raise
    os.chdir(mods_path.get())

    if len(os.listdir(mods_path.get())) > 0:
        remove = messagebox.askyesno('既存のファイルの削除', 'modsフォルダに既にファイルが存在します。\n削除しますか？')
        if remove:
            for filename in os.listdir(mods_path.get()):
                try:
                    if os.path.isfile(f'{mods_path.get()}/{filename}'):
                        os.remove(f'{mods_path.get()}/{filename}')
                    else:
                        shutil.rmtree(f'{mods_path.get()}/{filename}')
                except PermissionError:
                    print(f'{filename} ファイルの削除に失敗しました。ファイルを開いていないか確認してください', file=sys.stderr)

    def downloader():
        run_button.config(state=tkinter.DISABLED)
        futures = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for mod in mods:
                check = mod_checks.get(mod['filename'])
                if check is not None and not check.get():
                    continue

                flag = False
                if Tag.ClientOnly.value in mod['tags']:
                    if not is_server.get():
                        flag = True
                elif Tag.ServerOnly.value in mod['tags']:
                    if is_server.get():
                        flag = True
                else:
                    flag = True
                if flag:
                    futures.append(
                        executor.submit(
                            download,
                            mod
                        )
                    )
        error = False
        for future in futures:
            try:
                future.result()
            except Exception:
                error = True
        if error:
            print('いくつかのmodのダウンロードに失敗しました')
        else:
            print('全てのmodのダウンロードが完了しました')
        run_button.config(state=tkinter.NORMAL)

    thread = Thread(target=downloader)
    thread.start()


with open('mods.json', encoding='utf-8') as f:
    mods = json.load(f)

FORGE_CDN = 'https://edge.forgecdn.net/files/{0}/{1}/{2}'
CURSEFORGE_PATTERN = re.compile(
    r'https://www.curseforge.com/minecraft/mc-mods/[^/]+/(files|download)/(?P<id>\d{7})'
)

main = tkinter.Tk()
main.title('modインストーラー')
height = 80
for mod in mods:
    if Tag.Optional.value in mod['tags']:
        height += 21
main.geometry(f'500x{height}')

main_frame = ttk.Frame(main)
main_frame.grid(column=0, row=0, padx=5, pady=5, sticky=tkinter.NSEW)

mods_path = tkinter.StringVar()
is_server = tkinter.BooleanVar(value=False)

row = 0
mods_label = ttk.Label(main_frame, text="modsフォルダ指定")
mods_label.grid(column=0, row=row, sticky=tkinter.W)
mods_entry = ttk.Entry(main_frame, textvariable=mods_path)
mods_entry.grid(column=1, row=row, sticky=tkinter.EW)
mods_button = ttk.Button(main_frame, text="参照", command=ask_mods_path)
mods_button.grid(column=2, row=row, sticky=tkinter.W)
row += 1

is_server_button = ttk.Checkbutton(main_frame, text='サーバーにインストール', variable=is_server)
is_server_button.grid(column=0, row=row, sticky=tkinter.W)
row += 1

mod_checks = {}
for mod in mods:
    if Tag.Optional.value in mod['tags']:
        button_variable = tkinter.StringVar()
        button = ttk.Checkbutton(
            main_frame,
            text=(
                f"{mod['filename']} をインストール (サーバーのみ)"
                if Tag.ServerOnly.value in mod['tags'] else
                f"{mod['filename']} をインストール"
            ),
            variable=button_variable
        )
        button.grid(column=0, row=row, sticky=tkinter.W)
        row += 1
        mod_checks[mod['filename']] = button_variable

run_button = ttk.Button(main_frame, text="インストール", command=run)
run_button.grid(column=0, columnspan=3, row=row, sticky=tkinter.EW)

main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

main.mainloop()
