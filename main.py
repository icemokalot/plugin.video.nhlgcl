import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
from datetime import date, datetime, timedelta
import urllib, urllib2
from urllib2 import URLError, HTTPError
import json
import cookielib
import time
from bs4 import BeautifulSoup 
from resources.lib.globals import *


def categories():      
    addDir('Today\'s Games','/live',100,ICON,FANART)
    addDir('Yesterday\'s Games','/live',105,ICON,FANART)
    addDir('Goto Date','/date',200,ICON,FANART)
    addDir('NHL Videos','/qp',300,ICON,FANART)  
        

def todaysGames(game_day):    
    print "GAME DAY = " + str(game_day)            
    settings.setSetting(id='stream_date', value=game_day)    

    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                

    addDir('[B]<< Previous Day[/B]','/live',101,PREV_ICON,FANART,prev_day.strftime("%Y-%m-%d"))

    date_display = '[B][I]'+ colorString(display_day.strftime("%A, %m/%d/%Y"),GAMETIME_COLOR)+'[/I][/B]'
    addDir(date_display,'/nothing',999,ICON,FANART)

    #url = 'https://statsapi.web.nhl.com/api/v1/schedule?teamId=&startDate=2016-02-09&endDate=2016-02-09&expand=schedule.teams,schedule.linescore,schedule.game.content.media.epg,schedule.broadcasts,schedule.scoringplays,team.leaders,leaders.person,schedule.ticket,schedule.game.content.highlights.scoreboard,schedule.ticket&leaderCategories=points'
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.teams,schedule.linescore,schedule.scoringplays,schedule.game.content.media.epg&date='+game_day+'&site=en_nhl&platform=playstation'    
    req = urllib2.Request(url)    
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_PS4)

    try:    
        response = urllib2.urlopen(req)            
        json_source = json.load(response)                           
        response.close()                
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code          
        sys.exit()

    try:
        for game in json_source['dates'][0]['games']:        
            createGameListItem(game, game_day)
    except:
        pass
    
    next_day = display_day + timedelta(days=1)
    addDir('[B]Next Day >>[/B]','/live',101,NEXT_ICON,FANART,next_day.strftime("%Y-%m-%d"))
    #xbmc.executebuiltin("Container.SetViewMode(504)")

def createGameListItem(game, game_day):
    away = game['teams']['away']['team']
    home = game['teams']['home']['team']
    #http://nhl.cdn.neulion.net/u/nhlgc_roku/images/HD/NJD_at_BOS.jpg
    #icon = 'http://nhl.cdn.neulion.net/u/nhlgc_roku/images/HD/'+away['abbreviation']+'_at_'+home['abbreviation']+'.jpg'
    icon = 'http://raw.githubusercontent.com/eracknaphobia/game_images/master/square_black/'+away['abbreviation']+'vs'+home['abbreviation']+'.png'


    
    if TEAM_NAMES == "1":
        away_team = away['teamName']
        home_team = home['teamName']
    elif TEAM_NAMES == "2":
        away_team = away['name']
        home_team = home['name']
    elif TEAM_NAMES == "3":
        away_team = away['abbreviation']
        home_team = home['abbreviation']
    else:
        away_team = away['locationName']
        home_team = home['locationName']


    if away_team == "New York":
        away_team = away['name']

    if home_team == "New York":
        home_team = home['name']


    fav_game = False
    if away['locationName'].encode('utf-8') == FAV_TEAM or away['name'].encode('utf-8') == FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team,getFavTeamColor())           
    
    if home['locationName'].encode('utf-8') == FAV_TEAM or home['name'].encode('utf-8') == FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team,getFavTeamColor())


    game_time = ''
    if game['status']['detailedState'] == 'Scheduled':
        game_time = game['gameDate']
        game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%SZ")
        game_time = UTCToLocal(game_time)
       
        if TIME_FORMAT == '0':
             game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
             game_time = game_time.strftime('%H:%M')

        game_time = colorString(game_time,UPCOMING)            

    else:
        game_time = game['status']['detailedState']

        if game_time == 'Final':
            #if (NO_SPOILERS == '1' and game_time[:5] == "Final") or (NO_SPOILERS == '2' and game_time[:5] == "Final" and fav_game):
            #game_time = game_time[:5]                     
            game_time = colorString(game_time,FINAL)
        elif 'In Progress' in game_time:
            color = LIVE
            if 'Critical' in game_time:
                color = CRITICAL
            game_time = game['linescore']['currentPeriodTimeRemaining']+' '+game['linescore']['currentPeriodOrdinal']
            game_time = colorString(game_time,color)
        else:            
            game_time = colorString(game_time,LIVE)
        
        
    game_id = str(game['gamePk'])

    #live_video = game['gameLiveVideo']
    epg = json.dumps(game['content']['media']['epg'])
    live_feeds = 0
    archive_feeds = 0
    teams_stream = away['abbreviation'] + home['abbreviation']    
    stream_date = str(game['gameDate'])
      
     
    desc = ''       
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status']['detailedState'] == 'Scheduled':
        name = game_time + ' ' + away_team + ' at ' + home_team    
    else:
        name = game_time + ' ' + away_team + ' ' + colorString(str(game['teams']['away']['score']),SCORE_COLOR) + ' at ' + home_team + ' ' + colorString(str(game['teams']['home']['score']),SCORE_COLOR)         
        try:            
            soup = BeautifulSoup(str(game['content']['editorial']['recap']['items'][0]['preview']))
            desc = soup.get_text()
        except:
            pass

    fanart = None   
    try:        
        if game_day < localToEastern():
            fanart = str(game['content']['media']['epg'][3]['items'][0]['image']['cuts']['1136x640']['src'])
        else:
            '''
            GET https://statsapi.web.nhl.com/api/v1/game/2015020839/content?site=en_nhl HTTP/1.1
            Host: statsapi.web.nhl.com
            Connection: keep-alive
            User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36
            Origin: https://www.nhl.com
            Accept: */*
            Referer: https://www.nhl.com/gamecenter/phi-vs-nyr/2016/02/14/2015020839
            Accept-Encoding: gzip, deflate, sdch
            Accept-Language: en-US,en;q=0.8
            '''
            url = 'http://statsapi.web.nhl.com/api/v1/game/'+str(game['gamePk'])+'/content?site=en_nhl'
            req = urllib2.Request(url)    
            req.add_header('Connection', 'close')
            req.add_header('User-Agent', UA_PS4)

            try:    
                response = urllib2.urlopen(req)            
                json_source = json.load(response)     
                fanart = str(json_source['editorial']['preview']['items'][0]['media']['image']['cuts']['1284x722']['src'])                      
                response.close()                
            except HTTPError as e:
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code                                  
    except:
        pass

    name = name.encode('utf-8')
    if fav_game:
        name = '[B]'+name+'[/B]'
    
    title = away_team + ' at ' + home_team
    title = title.encode('utf-8')

    #Label free game of the day if applicable
    #if bool(game['content']['media']['epg'][0]['items'][0]['freeGame']) and game_day >= localToEastern():
    #name = name + colorString(" Free", FREE)
    
    #Set audio/video info based on stream quality setting

    audio_info, video_info = getAudioVideoInfo()
    #'duration':length
    info = {'plot':desc,'tvshowtitle':'NHL','title':title,'originaltitle':title,'aired':game_day,'genre':'Sports'}
    
    addStream(name,'',title,game_id,epg,icon,fanart,info,video_info,audio_info,teams_stream,stream_date)



def streamSelect(game_id, epg, teams_stream, stream_date):
    #print epg
    #0 = NHLTV
    #1 = Audio
    #2 = Extended Highlights
    #3 = Recap
    
    epg = json.loads(epg)    
    full_game_items = epg[0]['items']
    audio_items = epg[1]['items']
    highlight_items = epg[2]['items']
    recap_items = epg[3]['items']

    stream_title = []
    content_id = []
    event_id = []
    free_game = []
    media_state = []
    archive_type = ['Recap','Extended Highlights','Full Game']    
    
    multi_angle = 0
    multi_cam = 0
    if len(full_game_items) > 0:
        for item in full_game_items:
            media_state.append(item['mediaState'])

            if item['mediaFeedType'].encode('utf-8') == "COMPOSITE":
                multi_cam += 1
                stream_title.append("Multi-Cam " + str(multi_cam))
            elif item['mediaFeedType'].encode('utf-8') == "ISO":
                multi_angle += 1
                stream_title.append("Multi-Angle " + str(multi_angle))
            else:
                temp_item = item['mediaFeedType'].encode('utf-8').title()
                if item['callLetters'].encode('utf-8') != '':
                    temp_item = temp_item+' ('+item['callLetters'].encode('utf-8')+')'

                stream_title.append(temp_item)

            content_id.append(item['mediaPlaybackId'])
            event_id.append(item['eventId'])
            free_game.append(item['freeGame'])

    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)        

    
    #Reverse Order for display purposes
    #stream_title.reverse()
    #ft.reverse()
    print "MEDIA STATE"
    print media_state

    stream_url = ''
    media_auth = ''

    if media_state[0] == 'MEDIA_ARCHIVE':
        dialog = xbmcgui.Dialog() 
        a = dialog.select('Choose Archive', archive_type)
        if a < 2:
            if a == 0:
                #Recap                 
                try:            
                    stream_url = createHighlightStream(recap_items[0]['playbacks'][3]['url'])                
                except:
                    pass
            elif a == 1:
                #Extended Highlights                
                try:
                    stream_url = createHighlightStream(highlight_items[0]['playbacks'][3]['url'])
                except:
                    pass
        elif a == 2:
            dialog = xbmcgui.Dialog() 
            n = dialog.select('Choose Stream', stream_title)
            if n > -1:                
                stream_url, media_auth = fetchStream(game_id, content_id[n],event_id[n])                   
                stream_url = createFullGameStream(stream_url,media_auth,media_state[n])    
    else:
        dialog = xbmcgui.Dialog() 
        n = dialog.select('Choose Stream', stream_title)
        if n > -1:            
            stream_url, media_auth = fetchStream(game_id, content_id[n],event_id[n])
            stream_url = createFullGameStream(stream_url,media_auth,media_state[n])            
       
    
    listitem = xbmcgui.ListItem(path=stream_url)

    if stream_url != '':            
        listitem.setMimeType("application/x-mpegURL")
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)        
    else:        
        xbmcplugin.setResolvedUrl(addon_handle, False, listitem)        
        

def createHighlightStream(stream_url):
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)') 
    #Switch to ipad master file
    stream_url = stream_url.replace('master_wired.m3u8', MASTER_FILE_TYPE)

    if bandwidth != '':
        stream_url = stream_url.replace(MASTER_FILE_TYPE, 'asset_'+bandwidth+'k.m3u8')
        stream_url = stream_url + '|User-Agent='+UA_PS4

    print stream_url
    return stream_url


def createFullGameStream(stream_url, media_auth, media_state):
    #SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)        
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)')

    #Only set bandwidth if it's explicitly set
    if bandwidth != '':
        #Reduce convert bandwidth if composite video selected   
        if ('COMPOSITE' in stream_url or 'ISO' in stream_url) :
            if int(bandwidth) == 5000:
                bandwidth = '3500'
            elif int(bandwidth) == 1200:
                bandwidth = '1500'
        
        if media_state == 'MEDIA_ARCHIVE':                
            #ARCHIVE
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete-trimmed.m3u8') 

        elif media_state == 'MEDIA_ON':
            #LIVE    
            #5000K/5000_slide.m3u8 OR #3500K/3500_complete.m3u8
            # Slide = Live, Complete = Watch from beginning?
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete.m3u8') 
                
    
    cj = cookielib.LWPCookieJar()
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

    cookies = ''
    for cookie in cj:            
        if cookie.name == "Authorization":
            cookies = cookies + cookie.name + "=" + cookie.value + "; "
    #stream_url = stream_url + '|User-Agent='+UA_PS4+'&Cookie='+cookies+media_auth
    stream_url = stream_url + '|User-Agent='+UA_PS4+'&Cookie='+cookies+media_auth

    print "STREAM URL: "+stream_url
    return stream_url
    
                
def getAuthCookie():
    authorization = ''    
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))     
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)    

        #If authorization cookie is missing or stale, perform login    
        for cookie in cj:            
            if cookie.name == "Authorization" and not cookie.is_expired():            
                authorization = cookie.value 
    except:
        pass

    return authorization


def fetchStream(game_id, content_id,event_id):        
    stream_url = ''
    media_auth = ''    
   
    authorization = getAuthCookie()            
    
    if authorization == '':  
        login()
        authorization = getAuthCookie()   
        if authorization == '':
            return stream_url, media_auth

    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)         
    session_key = getSessionKey(game_id,event_id,content_id,authorization)    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))   
        

    if session_key == '':
        return stream_url, media_auth
    elif session_key == 'blackout':
        msg = "The game you are trying to access is not currently available due to local or national blackout restrictions.\n Full game archives will be available 48 hours after completion of this game."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Game Blacked Out', msg) 
        return stream_url, media_auth

    #Org
    url = 'https://mf.svc.nhl.com/ws/media/mf/v2.4/stream?contentId='+content_id+'&playbackScenario=HTTP_CLOUD_TABLET_60&platform=IPAD&sessionKey='+urllib.quote_plus(session_key)    
    req = urllib2.Request(url)       
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("Accept-Language", "en-US,en;q=0.8")                       
    req.add_header("Connection", "keep-alive")
    req.add_header("Authorization", authorization)
    req.add_header("User-Agent", UA_NHL)
    req.add_header("Proxy-Connection", "keep-alive")        


    response = opener.open(req)
    json_source = json.load(response)       
    response.close()
       

    if json_source['status_code'] == 1:
        if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
            msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Game Blacked Out', msg) 
        else:
            stream_url = json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url']    
            media_auth = str(json_source['session_info']['sessionAttributes'][0]['attributeName']) + "=" + str(json_source['session_info']['sessionAttributes'][0]['attributeValue'])
            session_key = json_source['session_key']
            settings.setSetting(id='media_auth', value=media_auth) 
            #Update Session Key
            settings.setSetting(id='session_key', value=session_key)   
    else:
        msg = json_source['status_message']
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Error Fetching Stream', msg)
       
    
    return stream_url, media_auth    
   



def getSessionKey(game_id,event_id,content_id,authorization):    
    #session_key = ''
    session_key = str(settings.getSetting(id="session_key"))

    if session_key == '':        
        epoch_time_now = str(int(round(time.time()*1000)))    

        url = 'https://mf.svc.nhl.com/ws/media/mf/v2.4/stream?eventId='+event_id+'&format=json&platform=WEB_MEDIAPLAYER&subject=NHLTV&_='+epoch_time_now        
        req = urllib2.Request(url)       
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "deflate")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                       
        req.add_header("Connection", "keep-alive")
        req.add_header("Authorization", authorization)
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "https://www.nhl.com")
        req.add_header("Referer", "https://www.nhl.com/tv/"+game_id+"/"+event_id+"/"+content_id)
        
        response = urllib2.urlopen(req)
        json_source = json.load(response)   
        response.close()
        
        print "REQUESTED SESSION KEY"
        if json_source['status_code'] == 1:      
            if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
                msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
                session_key = 'blackout'
            else:    
                session_key = str(json_source['session_key'])
                settings.setSetting(id='session_key', value=session_key)                              
        else:
            msg = json_source['status_message']
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Error Fetching Stream', msg)            
    
    return session_key  
    

def login():    
    #Check if username and password are provided    
    global USERNAME
    if USERNAME == '':        
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)        
        settings.setSetting(id='username', value=USERNAME)

    global PASSWORD
    if PASSWORD == '':        
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)

   
    if USERNAME != '' and PASSWORD != '':        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))   

        try:
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        except:
            pass

        #Get Token
        url = 'https://user.svc.nhl.com/oauth/token?grant_type=client_credentials'
        req = urllib2.Request(url)       
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "gzip, deflate, sdch")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                                           
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "https://www.nhl.com")
        #from https:/www.nhl.com/tv?affiliated=NHLTVLOGIN
        req.add_header("Authorization", "Basic d2ViX25obC12MS4wLjA6MmQxZDg0NmVhM2IxOTRhMThlZjQwYWM5ZmJjZTk3ZTM=")

        response = opener.open(req, '')
        json_source = json.load(response)   
        authorization = getAuthCookie()
        if authorization == '':
            authorization = json_source['access_token']
        response.close()
 
        if ROGERS_SUBSCRIBER == 'true':                        
            url = 'https://activation-rogers.svc.nhl.com/ws/subscription/flow/rogers.login'            
            login_data = '{"rogerCredentials":{"email":"'+USERNAME+'","password":"'+PASSWORD+'"}}'
            #referer = "https://www.nhl.com/login/rogers"              
        else:                   
            url = 'https://gateway.web.nhl.com/ws/subscription/flow/nhlPurchase.login'            
            login_data = '{"nhlCredentials":{"email":"'+USERNAME+'","password":"'+PASSWORD+'"}}'


        req = urllib2.Request(url, data=login_data, headers=
            {"Accept": "*/*",
             "Accept-Encoding": "gzip, deflate",
             "Accept-Language": "en-US,en;q=0.8",
             "Content-Type": "application/json",                            
             "Origin": "https://www.nhl.com",
             "Authorization": authorization,
             "Connection": "keep-alive",
             "User-Agent": UA_PC})     
       
        try:
            response = opener.open(req) 
        except HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code    
            print url   
            
            #Error 401 for invalid login
            if e.code == 401:
                msg = "Please check that your username and password are correct"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Invalid Login', msg)

        #response = opener.open(req)              
        #user_data = response.read()
        response.close()
      

        cj.save(ignore_discard=True); 


def logout(display_msg=None):    
    from resources.lib.globals import *
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))   
    try:  
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    except:
        pass
        
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))                
    url = 'https://account.nhl.com/ui/rest/logout'
    
    req = urllib2.Request(url, data='',
          headers={"Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-US,en;q=0.8",
                    "Content-Type": "application/x-www-form-urlencoded",                            
                    "Origin": "https://account.nhl.com/ui/SignOut?lang=en",
                    "Connection": "close",
                    "User-Agent": UA_PC})

    try:
        response = opener.open(req) 
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code    
        print url 

    #response = opener.open(req)              
    #user_data = response.read()
    response.close()
  
    #Clear session key and media auth variables
    #settings.setSetting(id='session_key', value='') 
    

    #clear session cookies since they're no longer valid    
    #cj.clear()
    #cj.save(ignore_discard=True);   

    if display_msg == 'true':
        settings.setSetting(id='session_key', value='') 
        dialog = xbmcgui.Dialog() 
        title = "Logout Successful" 
        dialog.notification(title, 'Logout completed successfully', ICON, 5000, False) 


def nhlVideos():    
    url = 'http://nhl.bamcontent.com/nhl/en/section/v1/video/nhl/ios-tablet-v1.json'    
    req = urllib2.Request(url)   
    req.add_header('User-Agent', UA_IPAD)
    
    try:    
        response = urllib2.urlopen(req)    
        json_source = json.load(response)                           
        response.close()                
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code          
        sys.exit()
    
    for video in json_source['videosLongList']:
        title = video['headline']
        name = title
        icon = video['image']['1136x640']
        url = video['mediaPlaybackURL']
        desc = video['blurb']
        release_date = video['date'][0:10]
        duration = video['duration']

        bandwidth = find(QUALITY,'(',' kbps)')
        url = url.replace('master_tablet60.m3u8', 'asset_'+bandwidth+'k.m3u8')
        url = url + '|User-Agent='+UA_IPAD

        audio_info, video_info = getAudioVideoInfo()
        info = {'plot':desc,'tvshowtitle':'NHL','title':name,'originaltitle':name,'duration':'','aired':release_date}
        addLink(name,url,title,icon,info,video_info,audio_info,icon)

    #xbmc.executebuiltin("Container.SetViewMode(504)")

params=get_params()
url=None
name=None
mode=None
game_day=None
game_id=None
epg=None
teams_stream=None
stream_date=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    game_day=urllib.unquote_plus(params["game_day"])
except:
    pass
try:
    game_id=urllib.unquote_plus(params["game_id"])
except:
    pass
try:
    epg=urllib.unquote_plus(params["epg"])
except:
    pass
try:
    teams_stream=urllib.unquote_plus(params["teams_stream"])
except:
    pass
try:
    stream_date=urllib.unquote_plus(params["stream_date"])
except:
    pass


print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)



if mode==None or url==None:        
    categories()  
elif mode == 100:      
    #Todays Games
    todaysGames(game_day)         
elif mode == 101:
    #Prev and Next 
    todaysGames(game_day)    
elif mode == 104:    
    streamSelect(game_id, epg, teams_stream, stream_date)
elif mode == 105:
    #Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                
    todaysGames(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:
    #Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)
    print game_day
    mat=re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)        
    if mat is not None:    
        todaysGames(game_day)
    else:    
        if game_day != '':    
            msg = "The date entered is not in the format required."
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Invalid Date', msg)

        sys.exit()        

elif mode == 300:
    nhlVideos()
elif mode == 400:    
    logout('true')
    
elif mode == 999:
    sys.exit()


if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)