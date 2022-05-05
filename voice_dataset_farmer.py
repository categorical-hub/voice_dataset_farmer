from __future__ import unicode_literals
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from pydub import AudioSegment
from pydub.utils import which
from pytube import YouTube
from glob import glob
import youtube_dl
import time
import os


class VocalDatasetFarmer:
    __status = 'pre-init'
    __output_path = 'dataset/'
    __work_path = 'data/'

    __ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    def __init__(self, url):
        self.url = url
        self.links = None
        print(self.__output_path)
        self.run()

    def __str__(self):
        return f'{self.url} Farmer. Status: {self.__status}'

    # TODO: add exceptions
    def __playlist_to_item(self):
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.set_window_size(1024, 600)
        driver.maximize_window()
        driver.get(self.url)
        time.sleep(2)

        soup = bs(driver.page_source, 'html.parser')
        res = soup.find_all('ytd-playlist-panel-video-renderer')
        self.links = [x.contents[1]['href'] for x in res]
        self.status = '__playlist_to_item complete'

    def __download_sound_and_captions(self):
        if not self.links:
            self.status = 'error - no links resolved from playlist.'
            return

        for link in self.links:
            direct_link = None
            direct_link = link[:link.find('&')]

            # get transcript
            source = YouTube('https://www.youtube.com' + link)
            caption = list(source.captions)
            caption_xml = caption[0].xml_captions

            f = open('data/' + direct_link[9:] + '.txt', 'w', encoding='utf-8')
            f.writelines(caption_xml)
            f.close()

            self.__ydl_opts['outtmpl'] = 'data/' + direct_link[9:] + '.mp3'

            with youtube_dl.YoutubeDL(self.__ydl_opts) as ydl:
                if direct_link:
                    ydl.download(['http://www.youtube.com' + direct_link])
                else:
                    ydl.download(['http://www.youtube.com' + link])

    def __segment_audio_by_captions(self):
        for file in glob(self.__work_path + '*.txt'):
            data_file = open(file, 'r', encoding='utf-8').read()
            filename = os.path.basename(file)
            soup = bs(data_file, features="xml")
            page = soup.findAll('p')

            all_segments = []

            for text_line in page:
                t = int(text_line.get('t'))
                d = int(text_line.get('d'))
                text = text_line.get_text().replace('\n', ' ')
                all_segments.append((text, t, d))

            # importing file from location by giving its path
            AudioSegment.converter = which("ffmpeg")
            sound = AudioSegment.from_file(file[:-3] + 'mp3', format="mp4")
            index = 0
            for segment in all_segments:
                extract = sound[segment[1] - 400:segment[1] + segment[2]]
                # Saving file in required location
                extract.export("dataset/" + filename[:-4] + '_' + str(index) + '.wav', format="wav")
                f = open("dataset/" + filename[:-4] + '_' + str(index) + '.txt', 'w', encoding='utf-8')
                f.write(segment[0])
                f.close()
                index += 1

    def run(self):
        try:
            self.__playlist_to_item()
            self.__download_sound_and_captions()
            self.__segment_audio_by_captions()
        except Exception as ex:
            print(ex)

    def save_dataset(self):
        print(f'saving dataset: {self.__output_path}')
        return


a = VocalDatasetFarmer('https://www.youtube.com/watch?v=xcXpKgjBxVE&list=PL51YAgTlfPj73SHVCnwQKWNY43qvGdQZu')
a.save_dataset()
