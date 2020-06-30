import subprocess
import os.path
from threading import Thread
from queue import Queue, Empty
import signal
from urllib.request import Request
import time

class Job():
    def __init__(self, manager, url, video_id, option_id, output_filename, output_dir, output_suffix=0, id=0):
        self.manager = manager
        self.url = url
        self.video_id = video_id
        self.option_id = option_id
        self.output_filename = output_filename
        self.output_dir = output_dir
        self.output_suffix = output_suffix
        self.id = id
        m3u8 = None
        done = False
        for video in Job.get_options(manager, url):
            if 'id' not in video:
                continue
            if not video['id'] == video_id:
                continue
            for option in video['formats']:
                if 'format_id' not in option:
                    continue
                if option['format_id'] == option_id:
                    self.title = video['title']
                    self.format = option
                    m3u8 = option['url']
                    done = True
                    break
            if done:
                break

        if not done:
            raise LookupError('Could not find video format requested')

        self.output_path = self.get_output_path()

        command_line = ['ffmpeg',
            '-i', m3u8,
            '-headers', Job.get_cookies(manager, m3u8),
            '-bsf:a', 'aac_adtstoasc',
            '-vcodec', 'copy',
            '-c', 'copy',
            self.output_path]
        self.queue = Queue()
        self.ended_at = -1
        self.start_process(command_line)
        self.enqueue_threads = []
        self.start_output_thread(self.process.stdout)
        self.start_output_thread(self.process.stderr)

    def get_output_path(self):
        return os.path.join(self.output_dir, '{}.mp4'.format(self.output_filename) if self.output_suffix < 1 else '{}_{}.mp4'.format(self.output_filename, self.output_suffix))

    @staticmethod
    def get_options(jobmanager, url):
        with jobmanager.youtube_dl_lock:
            result = jobmanager.youtube_dl.extract_info(url, download=False)
            if isinstance(result, list):
                return result
            else:
                return [result]

    @staticmethod
    def get_cookies(jobmanager, url):
        req = Request(url)
        with jobmanager.youtube_dl_lock:
            jobmanager.youtube_dl.cookiejar.add_cookie_header(req)
        return 'Cookie: {}\r\n'.format(req.get_header('Cookie'))

    def enqueue_output(self, out):
        for line in iter(out.readline, b''):
            self.queue.put(line.decode('utf-8'))
        out.close()
        self.ended_at = time.time()

    def start_output_thread(self, stream):
        t = Thread(target=Job.enqueue_output, args=(self, stream))
        t.daemon = True
        t.start()
        self.enqueue_threads.append(t)

    def start_process(self, command_line):
        self.process = subprocess.Popen(command_line, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.output_log = ''
        self.started_at = time.time()

    def uptime(self):
        if self.alive():
            return time.time() - self.started_at
        else:
            return self.ended_at - self.started_at

    def nice_uptime(self):
        tmp = self.uptime()
        return '{:1.0f}h {:1.0f}m {:1.2f}s'.format(tmp // 3600, (tmp // 60) % 60, tmp % 60)

    def nice_uptime2(self, use_tag=False, tag='samp'):
        tmp = self.nice_uptime()
        if use_tag:
            tmp = '<{}>{}</{}>'.format(tag, tmp, tag)
        if self.alive():
            return 'Running for {}'.format(tmp)
        else:
            return 'Ran for {}'.format(tmp)

    def update_logs(self):
        try:
            while True:
                line = self.queue.get_nowait()
                self.output_log = self.output_log + line
        except Empty:
            pass

    def get_log(self):
        self.update_logs()
        return self.output_log

    def stop(self):
        self.process.send_signal(signal.SIGINT)
    
    def alive(self):
        return self.process.poll() is None