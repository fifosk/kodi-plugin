# -*- coding: utf-8 -*-
import os, sys, urllib.parse
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE  = sys.argv[0]
QS    = sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2].startswith('?') else ''
PARAMS = {k:v[0] for k,v in urllib.parse.parse_qs(QS).items()}
ALLOWED_EXTS = {'.srt','.ass','.ssa','.vtt','.sub','.idx','.smi','.aqt','.pjs','.mpl','.jss','.rt','.txt'}

def translate(path): 
    try: return xbmcvfs.translatePath(path)
    except Exception: return path

def walk_subs(root, recursive=True):
    root = translate(root)
    if not xbmcvfs.exists(root): return
    if recursive:
        stack=[root]
        while stack:
            cur=stack.pop()
            dirs, files = xbmcvfs.listdir(cur)
            for d in dirs: stack.append(os.path.join(cur,d))
            for f in files:
                if os.path.splitext(f)[1].lower() in ALLOWED_EXTS:
                    yield os.path.join(cur,f)
    else:
        _, files = xbmcvfs.listdir(root)
        for f in files:
            if os.path.splitext(f)[1].lower() in ALLOWED_EXTS:
                yield os.path.join(root,f)

def list_files():
    subs_dir = ADDON.getSettingString('subs_dir') or 'special://home/subtitles'
    recursive = ADDON.getSettingBool('recursive')
    found = False
    for path in walk_subs(subs_dir, recursive):
        label=os.path.basename(path) or path
        li=xbmcgui.ListItem(label=label, label2=os.path.dirname(path))
        li.setProperty('sync','true')
        li.setProperty('hearing_imp','false')
        li.setProperty('language','')
        url=f"{BASE}?action=apply&path={urllib.parse.quote(path, safe='')}"
        xbmcplugin.addDirectoryItem(handle=HANDLE,url=url,listitem=li,isFolder=False)
        found=True
    xbmcplugin.endOfDirectory(HANDLE,succeeded=True,cacheToDisc=False)
    if not found:
        xbmcgui.Dialog().notification('Local Subtitles','No files found',xbmcgui.NOTIFICATION_INFO,3000)

def apply_file(qpath):
    path=urllib.parse.unquote(qpath)
    if not xbmcvfs.exists(path):
        xbmcgui.Dialog().notification('Local Subtitles','File not found',xbmcgui.NOTIFICATION_ERROR,3000)
        return
    try:
        xbmc.Player().showSubtitles(True)
        xbmc.Player().setSubtitles(path)
        xbmcgui.Dialog().notification('Local Subtitles', os.path.basename(path), xbmcgui.NOTIFICATION_INFO, 2500)
        listitem = xbmcgui.ListItem(path=path)
        listitem.setMimeType('text/plain')
        listitem.setContentLookup(False)
        xbmcplugin.setResolvedUrl(HANDLE, True, listitem)
    except Exception as exc:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        xbmcgui.Dialog().ok('Local Subtitles', f'Failed:\n{path}\n\n{exc}')

if __name__ == "__main__":
    action=PARAMS.get('action','list')
    if action=='apply':
        apply_file(PARAMS.get('path',''))
    else:
        list_files()
