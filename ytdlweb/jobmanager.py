from threading import Lock
from youtube_dl import YoutubeDL
from .job import Job

class JobManager():
    def __init__(self):
        self.jobs = []
        self.oldjobs = []
        ytdl_opts = {}
        self.youtube_dl = YoutubeDL(ytdl_opts)
        self.youtube_dl_lock = Lock()
        self.currentID = 1

    def get_job_by_id(self, id):
        job: Job
        for job in self.jobs:
            if job.id == id:
                return job
        for job in self.oldjobs:
            if job.id == id:
                return job
        return None

    def restart(self, job: Job):
        self.currentID += 1
        newJob = Job(self, job.url, job.video_id, job.option_id, job.output_filename, job.output_dir, output_suffix=job.output_suffix+1, id=self.currentID)
        self.jobs.append(newJob)
        self.update_jobs()
        return newJob

    def update_jobs(self):
        job: Job
        for idx, job in enumerate(self.jobs):
            if job is None:
                continue
            if not job.alive():
                if job.output_suffix > 3:
                    self.oldjobs.append(job)
                    self.jobs[idx] = None
                    continue
        self.jobs = [job for job in self.jobs if job is not None]

    def create_job(self, *args, **kwargs):
        self.currentID += 1
        job = Job(*args, **kwargs, id=self.currentID)
        self.jobs.append(job)
        self.update_jobs()
        return job

    def get_jobs(self):
        self.update_jobs()
        return self.jobs + self.oldjobs

    def dismiss(self, job_id):
        found = False
        for idx, job in enumerate(self.jobs):
            if job.id == job_id:
                if job.alive():
                    job.stop()
                self.jobs[idx] = None
                found = True
                break
        if not found:
            for idx, job in enumerate(self.oldjobs):
                if job.id == job_id:
                    if job.alive():
                        job.stop()
                    self.oldjobs[idx] = None
                    found = True
                    break
        self.update_jobs()