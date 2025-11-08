# -*- coding: utf-8 -*-
import hashlib, os, sys, urllib.parse
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo("version")


def ellipsize(text, limit=60):
    if len(text) <= limit:
        return text
    keep = (limit - 3) // 2
    return f"{text[:keep]}...{text[-keep:]}"
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
BASE  = sys.argv[0]
QS    = sys.argv[2][1:] if len(sys.argv) > 2 and sys.argv[2].startswith('?') else ''
PARAMS = {k:v[0] for k,v in urllib.parse.parse_qs(QS).items()}
ALLOWED_EXTS = {'.srt','.ass','.ssa','.vtt','.sub','.idx','.smi','.aqt','.pjs','.mpl','.jss','.rt','.txt'}
TEMP_SUB_DIR = 'special://temp/localfiles_subtitles'

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

def ensure_temp_storage():
    if not xbmcvfs.exists(TEMP_SUB_DIR):
        xbmcvfs.mkdir(TEMP_SUB_DIR)

def cache_subtitle(path):
    ensure_temp_storage()
    ext = os.path.splitext(path)[1] or '.srt'
    digest = hashlib.md5(path.encode('utf-8')).hexdigest()
    temp_name = f"{digest}{ext}"
    temp_path = f"{TEMP_SUB_DIR}/{temp_name}"
    if xbmcvfs.exists(temp_path):
        xbmcvfs.delete(temp_path)
    if not xbmcvfs.copy(path, temp_path):
        raise IOError(f"Failed to copy subtitle to {temp_path}")
    return temp_path

def list_files():
    subs_dir = ADDON.getSettingString('subs_dir') or 'special://home/subtitles'
    recursive = ADDON.getSettingBool('recursive')
    found = False
    if HANDLE >= 0:
        xbmcplugin.setPluginCategory(HANDLE, f"{ADDON.getAddonInfo('name')} v{ADDON_VERSION}")
    for path in walk_subs(subs_dir, recursive):
        filename=os.path.basename(path) or path
        li=xbmcgui.ListItem(
            label=filename,
            label2=filename,
        )
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
        cached_path = cache_subtitle(path)
        xbmc.Player().showSubtitles(True)
        xbmc.Player().setSubtitles(cached_path)
        xbmcgui.Dialog().notification(
            'Local Subtitles',
            f"{ellipsize(os.path.basename(path), 40)} • v{ADDON_VERSION}",
            xbmcgui.NOTIFICATION_INFO,
            2500,
        )
        listitem = xbmcgui.ListItem(path=cached_path)
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
