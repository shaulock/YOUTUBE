from pytube import YouTube, Playlist, Stream, Search
from datetime import datetime
from tabulate import tabulate
from colorama import init, just_fix_windows_console, Fore, Back, Style
from art import text2art
from pytube.exceptions import AgeRestrictedError as AGRE
from pytube.exceptions import ExtractError as EXTE
from pytube.exceptions import LiveStreamError as LVSE
from pytube.exceptions import MaxRetriesExceeded as MXRE
from pytube.exceptions import MembersOnly as MBOE
from pytube.exceptions import RegexMatchError as RGME
from pytube.exceptions import VideoPrivate as VDPE
from pytube.exceptions import VideoRegionBlocked as VRBE
from pytube.exceptions import VideoUnavailable as VDUE
from pytube.exceptions import PytubeError
from requests.exceptions import HTTPError as HTTE
from pytube.exceptions import RecordingUnavailable as RCUE
from icecream import ic
from sys import stdout as sto

MAIN_MENU = """
What will you like to do now?

1. I wanna search for some videos.
2. I'll give ya a video link, and we'll take it from there.
3. Look into the playlist that I am giving you the link for.
0. Exit.
"""

def make_link(uri: str, label: str='') -> str: # type: ignore
    if not label: 
        label = uri
    parameters = ''

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST 
    escape_mask = f'\033]8;{parameters};{uri}\033\\{label}\033]8;;\033\\'

    return escape_mask

def progress_bar(stream: Stream, _: bytes, bytes_remaining: int) -> None:
    current = ((stream.filesize - bytes_remaining)/stream.filesize)
    percent = ('{0:.1f}').format(current*100)
    progress = int(50*current)
    status = '█' * progress + '-' * (50 - progress)
    sto.write(f'{Fore.LIGHTGREEN_EX}{Back.BLACK}{Style.BRIGHT}\t|{status}| {percent}%\r{Style.RESET_ALL}')
    if not current == 100.0:
        sto.flush()

def download_video_complete(__: Stream, _:str) -> None:
    print_normal_message('\n\nDone!\n')
    print_normal_message(f'Download Stored Here : {f'{color_url(make_link(_, 'Location'))}'}')
    go_on()

def print_welcome(_: None=None) -> None:
    s1 = text2art('Welcome to ', 'tarty4')
    s2 = text2art('YouTube', 'tarty4')
    print(f'\n{Fore.CYAN}{Back.BLACK}{Style.BRIGHT}{s1}\n{Fore.RED}{s2}{Style.RESET_ALL}')

def print_error(s: str) -> None:
    print(f'{Fore.RED}{Back.BLACK}{Style.BRIGHT}{s}{Style.RESET_ALL}')

def convert_number_to_readable(n: int) -> str:
    readable = f'{f'{n%1000:03d}' if n//1000 > 0 else f'{n%1000}'}'
    n//=1000
    while n:
        readable = f'{f'{(n)%1000:03d}' if n//1000 > 0 else f'{n%1000}'},' + readable
        n//=1000
    return readable

def convert_seconds_to_more_readable(secs: int) -> str:
    seconds = secs % 60
    minutes = (secs // 60) % 60
    hours = ((secs // 60) // 60) % 24
    days = (((secs // 60) // 60) // 24) % 365
    years = (((secs // 60) // 60) // 24) // 365
    readable = ''
    if years:
        readable = readable + f' {years} Year{'s' if years > 1 else ''}'
    if days:
        readable = readable + f' {days} Day{'s' if days > 1 else ''}'
    if hours:
        readable = readable + f' {hours} Hour{'s' if hours > 1 else ''}'
    if minutes:
        readable = readable + f' {minutes} Minute{'s' if minutes > 1 else ''}'
    if seconds:
        readable = readable + f' {seconds} Second{'s' if seconds > 1 else ''}'    
    return readable.strip()

def color_table_element(s: str) -> str:
    return f'{Fore.LIGHTYELLOW_EX}{Back.BLACK}{Style.NORMAL}{s}{Style.RESET_ALL}'

def color_url(s: str) -> str:
    return f'{Fore.LIGHTCYAN_EX}{Back.BLACK}{Style.NORMAL}{s}{Style.RESET_ALL}'

def color_table_header(s: str) -> str:
    return f'{Fore.LIGHTMAGENTA_EX}{Back.BLACK}{Style.BRIGHT}{s}{Style.RESET_ALL}'

def print_video_info(yt: YouTube, headers: list=[]) -> None:
    available = False
    try:
        yt.check_availability()
        if yt.age_restricted:
            try:
                yt.bypass_age_gate()
            except AGRE:
                print_error('\nWhat kinda videos are you watching!?\nThis was age-restricted and I couldn\'t even bypass it!\n')
                go_on()
                print_bye()
        available = True
    except KeyboardInterrupt:
        print_bye()
    except (MBOE, LVSE, RCUE, VDUE, VDPE):
        pass
    try:
        details = [
            [color_table_header('Video Title'), color_url(make_link(yt.watch_url, yt.title))],
            [color_table_header('Number of views'), color_table_element(convert_number_to_readable(yt.views))],
            [color_table_header('Length of Video'), color_table_element(convert_seconds_to_more_readable(yt.length))],
            [color_table_header('Publish Date'), color_table_element(yt.publish_date.strftime("%B %d %Y"))], # type: ignore
            [color_table_header('Thumbnail URL'), color_url(make_link(yt.thumbnail_url, 'Thumbnail'))],
            [color_table_header('Channel'), color_url(make_link(yt.channel_url, yt.author))],
            [color_table_header('Available?'),color_table_element('Yes' if available else 'No')],
            [color_table_header('Age restricted?'), color_table_element('Yes' if yt.age_restricted else 'No')]
        ]
        print(tabulate(details, headers=headers))
    except KeyboardInterrupt:
        print_bye()
    except EXTE:
        print_error('\nWhoops! Couldn\'t Extract Something From The Video\n')
        go_on()
        print_bye()

def print_menu(s: str) -> None:
    print(f'{Fore.GREEN}{Back.BLACK}{Style.BRIGHT}{s}{Style.RESET_ALL}')

def print_normal_message(s: str) -> None:
    print(f'{Fore.YELLOW}{Back.BLACK}{Style.BRIGHT}{s}{Style.RESET_ALL}')

def print_bye(_: None=None) -> None:
    print_error('Interrupted through keyboard?!')
    print_bye_normal()

def print_bye_normal(_: None=None) -> None:
    print_normal_message('\nAlright! Whatever! Byee! Take Care!')
    exit(0)

def get_input(s: str) -> str:
    ip = ''
    try:
        ip = input(f'{Fore.BLUE}{Back.BLACK}{Style.BRIGHT}{s}{Fore.WHITE}')
        print(f'{Style.RESET_ALL}', end='')
    except KeyboardInterrupt:
        print_bye()
    return ip

def get_int(prompt: str, min: int=None, max: int=None, message: str=None) -> int: # type: ignore
    
    user_input = 0

    if not min and not min==0:
        min = '' # type: ignore
    if not max and not max==0:
        max = '' # type: ignore

    if isinstance(min, int) and isinstance(max, int):
        if min > max:
            min, max = max, min

    if not message:
        message = f"\nThe Input Was Not Within The Required Bounds [{min},{max}]\n"

    if not prompt:
        prompt = ''

    try:
        user_input = int(get_input(prompt))

    except ValueError:
        print_error("\nPlease Enter An Integer, I Don't Want Your Name\n")
        return get_int(prompt=prompt, 
                min=min, 
                max=max, 
                message=message)
    
    except KeyboardInterrupt:
        print_bye()
    
    if not min and not min==0:
        min = user_input - 1

    if not max and not max==0:
        max = user_input + 1

    if user_input < int(min) or user_input > int(max):
        print_error(message)
        return get_int(prompt=prompt, 
                min=min, 
                max=max, 
                message=message)
    
    else:
        return user_input


# def __str__(self, level=0) -> str:
#     to_return = "\t" * level + self.__repr__() + "\n" + '\t' * level + '{\n'
#     for child in self.children:
#         if child.type == LeafNode:
#             to_return += "\t" * (level + 1) + child.value + "\n"
#         else:
#             to_return += child.__str__(level+1)
#     return to_return + '\t' * level + '}\n'

def main_menu(_: None=None) -> int:
    args_for_main_menu_input = {
        'prompt': f'> ',
        'min': 0,
        'max': 3,
        'message': '\nStick to the options I gave you, please.\n'
    }
    print_menu(MAIN_MENU) # type: ignore
    return get_int(**args_for_main_menu_input)

def go_on(_: None=None) -> None:
    go_on_menu = """
Wanna go on or ya done?

1. Yeah, I am done. Too tired now.
2. Nah, I wanna stay in YouTube for a while longer.
"""
    print_menu(go_on_menu)
    choice = get_int('> ', 1, 2, '\nUgh! Put your glasses on grandpa!\n')
    if choice == 1:
        print_bye_normal()
    else:
        print_normal_message('\nAs you wish!')
        home_screen()

def do_oauth(yt: YouTube) -> tuple:
    oauth_menu = """
Wanna log in?

1. Yes, I don't care about my privacy.
2. No, what if you see all the wierd shit I watch?
"""
    print_menu(oauth_menu)
    oauth = get_int(prompt='> ',
                    min=1,
                    max=2,
                    message='\nDyslexic much? Look at the numbers beside the options.\n')
    if oauth == 1:
        yt.use_oauth = True
        yt.title
    else:
        print_normal_message('Fair enough! Keep your history safe, I guess.')
    return yt, oauth

def get_Object(type: str) -> YouTube | Playlist | None:
    match type:
        case 'YouTube':
            while True:      
                try:
                    link = get_input('\nPaste the link of the video here : ')
                    print()
                    yt = YouTube(link)
                except RGME:
                    print_error('\nAtleast paste a valid youtube video link, dork!\n')
                    continue
                try:
                    yt.check_availability()
                    return yt
                except VRBE:
                    print_error('\nLooks like the video is reagion blocked, mate! What a luck!\n')
                except MBOE:
                    print_error('\nThis video is members only! Can\'t help here!\n')
                    go_on()
                    print_bye_normal()
                except LVSE:
                    print_error('\nThis video is a live stream, man. Wait, till it is done streaming.\n')
                    go_on()
                    print_bye_normal()
                except RCUE:
                    print_error('\nWell, tough luck! The recording of this live stream doesn\'t exist!\n')
                    go_on()
                    print_bye_normal()
                except VDPE:
                    print_error('\nThis video is private! Don\'t be lurking on someone else\'s private life!\n')
                    print_menu("""
Is it your channel?
1. Yes
2. No
""")
                    own = get_int('> ', 1, 2, '\nDon\'t test my patience! You know what you did wrong!\n')
                    if own == 1:
                        yt, oauth = do_oauth(yt)
                        if oauth == 1:
                            return yt
                        else:
                            go_on()
                            print_bye_normal()
                    else:
                        print_normal_message('I knew you were a creep!!')
                        go_on()
                        print_bye_normal()
                except VDUE:
                    print_error('\nDid you copy the link correctly? This video don\'t exist, dumbass!\n')
                    go_on()
        case 'Playlist':
            return Playlist('')

def download_video(stream: Stream, yt: YouTube) -> None:
    try:
        file_extension = ''
        for i in range(1,len(stream.default_filename)+1):
            if stream.default_filename[-i] == '.':
                break
            file_extension = stream.default_filename[-i] + file_extension
        filename = f'{stream.title.replace(' ', '_')}_{f'{stream.resolution}_{stream.fps}fps_video_' if stream.includes_video_track else 'no_video_'}{f'{stream.abr}_audio_' if stream.includes_audio_track else 'no_audio_'}{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{file_extension}'
        yt.register_on_progress_callback(progress_bar)
        yt.register_on_complete_callback(download_video_complete) # type: ignore
        stream = yt.streams.get_by_itag(stream.itag) # type: ignore
        print_normal_message('\nDownloading...\n')
        try:
            stream.download(filename=filename,max_retries=9)
        except MXRE:
            print_error('\nWe tried very hard, and reached very far!\nBut in the end, it doesn\'t matter!\nConnection timed out.\n')
            go_on()
    except KeyboardInterrupt:
        print_bye()
    
def continue_search(search: Search) -> None:
    suggested_search_menu = """
Do you want to look for these?

"""
    suggestions = []
    try:
        suggestions = list(search.completion_suggestions) # type: ignore
    except KeyError:
        search_youtube() # type: ignore
    tick = len(suggestions) + 1
    suggested_search_menu = suggested_search_menu + '\n'.join([
        f'{i}. {s}' for i, s in enumerate(suggestions, 1)
    ])
    suggested_search_menu = suggested_search_menu + f"""
{tick}. Nope, you didn't get my search query right!
0. Just end this all man, I am done!
"""
    print_menu(suggested_search_menu)
    choice = get_int(
        '> ',
        min = 0,
        max = tick,
        message='\nWhy can\'t you just see what you actually have to enter!\n'
    )
    if not choice:
        print_bye_normal()
    for i, s in enumerate(suggestions, 1):
        if i == choice:
            search_youtube(Search(s))
    else:
        if choice == tick:
            print_normal_message('\nAlright! Sorry! My Bad!')
            search_youtube() # type: ignore

def search_youtube(search: Search=None) -> None: # type: ignore
    if not search:
        query = get_input('\nWhat are you looking for? ')
        search = Search(query)
    try:
        current_results = list(search.results) # type: ignore
        if not current_results:
            continue_search(search=search)
        is_first_iter = True
        while True:
            search_menu = """
What video do you wanna select?

"""
            if not is_first_iter:
                try:
                    current_results = search.get_next_results()
                except IndexError:
                    continue_search(search=search)
                    break
            if not current_results:
                continue_search(search=search)
                break
            results = []
            for i, yt in enumerate(current_results, 1): # type: ignore
                results.append([i, yt])
            number_of_results = len(results)
            search_menu = search_menu + '\n'.join([f'{i}. Video Number {i}' for i, _ in results])
            tick = number_of_results+1
            search_menu = search_menu + f"""
{tick}. Nope, not satisfied with the results, take me to next page
{tick+1}. These don't look like the correct results.
0. Nope, I want out! Now!
"""
            for i, yt in results:
                print()
                print_video_info(yt, headers=[color_table_header('Video Number'), color_table_element(f'{i}')])
            print_menu(search_menu)
            choice = get_int(
                '> ',
                min=0,
                max=tick+1,
                message='\nPlease! I beg you! I would kneel on your feet,\nbut you won\'t see it too\n'
            )
            for i, yt in results:
                if i == choice:
                    video_w_link(yt)
            else:
                if choice == tick:
                    is_first_iter = False
                    continue
                elif choice == tick+1:
                    continue_search(search=search)
                    break
                else:
                    print_bye_normal()
    except KeyboardInterrupt:
        print_bye()

def video_w_link(yt: YouTube=None) -> None: # type: ignore
    if not yt:
        yt = get_Object('YouTube') # type: ignore
    print_video_info(yt) # type: ignore

    yt_menu = """
What do you wanna do with this?

1. Download Audio (must be a ringtone, I guess)
2. Download Video (with Audio) (like a normal person)
3. Download Only Video (like a psycho)
0. Just wanted to Know the details, I am done. (Such a nerd)
"""
    print_menu(yt_menu)
    choice = get_int('> ', 0, 3, '\nOMG! Jesus Christ!\n')
    if not choice:
        go_on()
    streams = yt.streams
    stream_dict = {}
    for i, stream in enumerate(streams, 1):
        stream_dict[i] = stream
    table = []
    keys = []
    counter = 1
    if choice == 1:
        table = [
            [
                color_table_header('Option Number'), 
                '\n'.join([
                    color_table_header('Audio Quality'), 
                    color_table_header('(kbps)')
                    ]), 
                '\n'.join([
                    color_table_header('Bitrate'), 
                    color_table_header('(For the whole file)'), 
                    color_table_header('(bytes/second)')
                    ]),
                '\n'.join([
                    color_table_header('Size'), 
                    color_table_header('(MB)')
                    ])
            ]
        ]
        for key, value in stream_dict.items():
            if value.includes_audio_track and not value.includes_video_track:
                keys.append(key)
                table.append([
                    color_table_element(f'{counter}'), 
                    color_table_element(f'{value.abr}'), 
                    color_table_element(f'{value.bitrate}'), 
                    color_table_element(f'{value.filesize_mb:.3f}')
                    ])
                counter += 1
    if choice == 2:
        table = [
            [
                color_table_header('Option Number'), 
                '\n'.join([
                    color_table_header('Video Quality'), 
                    color_table_header('(Resolution FPS)')
                    ]), 
                '\n'.join([
                    color_table_header('Audio Quality'), 
                    color_table_header('(kbps)')
                    ]), 
                '\n'.join([
                    color_table_header('Bitrate'), 
                    color_table_header('(For the whole file)'), 
                    color_table_header('(bytes/second)')
                    ]), 
                '\n'.join([
                    color_table_header('Size'), 
                    color_table_header('(MB)')
                    ])
            ]
        ]
        for key, value in stream_dict.items():
            if value.includes_audio_track and value.includes_video_track:
                keys.append(key)
                table.append([
                    color_table_element(f'{counter}'), 
                    color_table_element(f'{value.resolution} {value.fps}fps'), 
                    color_table_element(f'{value.abr}'), 
                    color_table_element(f'{value.bitrate}'), 
                    color_table_element(f'{value.filesize_mb:.3f}')
                ])
                counter+=1
    if choice == 3:
        table = [
            [
                color_table_header('Option Number'), 
                '\n'.join([
                    color_table_header('Video Quality'), 
                    color_table_header('(Resolution FPS)')
                    ]),
                '\n'.join([
                    color_table_header('Bitrate'), 
                    color_table_header('(For the whole file)'), 
                    color_table_header('(bytes/second)')
                    ]), 
                '\n'.join([
                    color_table_header('Size'), 
                    color_table_header('(MB)')
                    ])
            ]
        ]
        for key, value in stream_dict.items():
            if not value.includes_audio_track and value.includes_video_track:
                keys.append(key)
                table.append([
                    color_table_element(f'{counter}'), 
                    color_table_element(f'{value.resolution} {value.fps}fps'), 
                    color_table_element(f'{value.bitrate}'), 
                    color_table_element(f'{value.filesize_mb:.3f}')
                ])
                counter+=1
    print()
    print(tabulate(table, headers="firstrow", floatfmt='.3f', numalign='left'))
    print()
    filtered_stream_dict = {}
    i = 1
    for key in keys:
        filtered_stream_dict[i] = stream_dict[key]
        i+=1
    choice = get_int(
        'Choose your option : ',
        1,
        len(filtered_stream_dict),
        "\nDon't angry me! If you want your file, enter the correct option\n"
    )
    stream = filtered_stream_dict[choice]
    download_video(stream, yt)

def playlist_w_link(pl: Playlist=None) -> None: # type: ignore
    if not Playlist:
        pl = get_Object('Playlist') # type: ignore
    playlist_name = pl.title
    playlist_owner = pl.owner
    playlist_link = pl.playlist_url
    pass
    

def home_screen(_: None=None) -> None: # type: ignore
    main_menu_choice=main_menu()
    while main_menu_choice:
        match main_menu_choice:
            case 1:
                search_youtube() # type: ignore
            case 2:
                video_w_link()
            case 3:
                playlist_w_link()

        main_menu_choice = main_menu()

def main(_: None=None) -> None:
    init()
    just_fix_windows_console()
    print_welcome()
    try:
        home_screen()
    except KeyboardInterrupt:
        print_bye()

    print_bye_normal()

if __name__ == '__main__':
    main()