from flask import Flask, render_template, request, redirect, url_for
from .jobmanager import JobManager
from .job import Job

class YTDLWeb():
    def __init__(self, name):
        app = Flask(name)
        self.manager = JobManager()
        self.output_dir = '.'

        @app.route('/')
        def home():
            return render_template('home.html', nav=self.nav)

        @app.route('/jobs')
        def jobs():
            return render_template('jobs.html', nav=self.nav, manager=self.manager, jobs=self.manager.get_jobs())

        @app.route('/jobs/<int:job_id>')
        def job(job_id):
            return render_template('job.html', nav=self.nav, manager=self.manager, job_id=job_id, job=self.manager.get_job_by_id(job_id))

        @app.route('/create', methods=['GET', 'POST'])
        def create():
            if request.method == 'GET':
                return render_template('create.html', nav=self.nav)
            else:
                if request.form['stage'] == 'create':
                    job = self.manager.create_job(
                        self.manager,
                        request.form['url'],
                        request.form['video_id'],
                        request.form['option_id'],
                        request.form['output_filename'],
                        self.output_dir
                    )
                    return redirect(url_for('job', job_id=job.id))
                else:
                    options = Job.get_options(self.manager, request.form['url'])
                    return render_template('create_options.html', nav=self.nav, options=options, url=request.form['url'])

        @app.route('/restart/<int:job_id>')
        def restart(job_id):
            job = self.manager.get_job_by_id(job_id)
            if job.alive():
                job.stop()
                return redirect(url_for('jobs'))
            else:
                newJob = self.manager.restart(job)
                return redirect(url_for('job', job_id=newJob.id))

        @app.route('/dismiss/<int:job_id>')
        def dismiss(job_id):
            self.manager.dismiss(job_id)
            return redirect(url_for('jobs'))

        self.nav = [
            {
                'href': '/jobs',
                'caption': 'Jobs'
            },
            {
                'href': '/create',
                'caption': 'Create'
            }
        ]

        app.run(threaded=True)