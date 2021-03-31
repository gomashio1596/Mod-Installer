# Mod Installer
Minecraftのmodを高速、簡単にインストールするためのプログラム  
mods.jsonにmodの情報を書き込む  
~~ダウンローダーじゃないの？~~  

# mods.json
[Mod Info](#Mod-Info) のリスト

## RPC Info
|  キー  |  型  |  説明  |
| --- | --- | --- |
|  filename  |  文字列 (String)  |  modのファイル名。`../config/example.cfg`等にすることもできる  |
|  url  |  文字列 (String)  |  modのダウンロードURL  |
|  mode  |  [Mode](#Mode)  |  modのインストール方法  |
|  tags  |  List[[Tag](#Tag)]  |  タグ  |

## Mode
|  値  |  説明  |
| --- | --- |
|  normal  |  ダウンロードしたファイルをそのまま導入する  |
|  extract  |  ダウンロードしたファイルを解凍、中身のファイルを同ディレクトリに展開する  |

## Tag
|  値  |  説明  |
| --- | --- |
|  client-only  |  クライアントモード時にのみインストール  |
|  server-only  |  サーバーモード時にのみインストール  |
|  optional  |  インストールするかどうかのチェックボックスを使用する  |
