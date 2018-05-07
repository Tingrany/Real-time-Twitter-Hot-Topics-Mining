import os
import random
import time
from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify
from celery import Celery
from datetime import datetime, timedelta


app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery = Celery(app.name)
celery.conf.update(app.config)


# @celery.task
# def send_async_email(msg):
#     """Background task to send an email with Flask-Mail."""
#     with app.app_context():
#         mail.send(msg)


@celery.task(bind=True)
def update_number(self, n, start):
    for i in range(n):
        print start+i
        self.update_state(state='PROGRESS', meta={'number': start+i})
        time.sleep(1)
    return {'number': start+i}


@celery.task(bind=True)
def update_topics(self):
    for i in range(10):
        read_file = open('setting.txt','r')
        setting = read_file.read()
        setting = eval(setting)
        current_time = time.time()
        date = datetime.fromtimestamp(current_time)
        print setting
        if 'time' in setting:
            # quick display mode
            date = datetime.fromtimestamp(setting['start_time'])
        try:
            result_files = []
            files = os.listdir("/Users/xkchen/Desktop/large data stream/project/tweet_hot_topic")
            for file_path in files:
                if os.path.isdir(file_path):
                    continue
                if file_path.split('.')[1] == 'txt' and len(file_path.split('_')) == 4:
                    result_files.append(file_path)
            result_files = sorted(result_files, key=lambda x: datetime.strptime(x.split('.')[0], '%b_%d_%H|%M_%Y'))
            for i in range(len(result_files)):
                if date < datetime.strptime(result_files[i].split('.')[0], '%b_%d_%H|%M_%Y'):
                    if i>0 and i:
                        i -= 1
                    break
            # update state using this file
            print 'data file', result_files[i]
            data_file = open(result_files[i], 'r')
            data = data_file.read()
            data = eval(data)
            new_topics = {}
            for topic in data['topics']:
                keywords = data['topics'][topic]
                tmp = ''
                # print keywords
                for key_word in keywords:
                    tmp = tmp + '(' + key_word[0] + ', ' + str(key_word[1]) + '),   '
                new_topics[topic] = tmp
            data['topics'] = new_topics
            self.update_state(state='PROGRESS', meta=data)
        except:
            print 'something wrong'
        if 'time' in setting:
            if setting['time_period'] > 0:
                setting['start_time'] += setting['time_interval']*60
                setting['time_period'] -= setting['time_interval']
                write_file = open('setting.txt', 'w')
                write_file.write(str(setting))
                write_file.close()
                print 'update setting success'
            else:
                write_file = open('setting.txt', 'w')
                write_file.write('{}')
                write_file.close()
            time.sleep(setting['display_interval'])
        else:
            time.sleep(0.5)
    return data


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@app.route('/updateNumber', methods=['GET', 'POST'])
def updateNumber():
    # task = update_number.apply_async(args=[10,8])
    task = update_topics.apply_async()
    return jsonify({}), 202, {'Location': url_for('numberStatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def numberStatus(task_id):
    # task = update_number.AsyncResult(task_id)
    task = update_topics.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'number': 0
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            # 'number': task.info.get('number', 0)
            'topic_number': task.info.get('topic_number', 0),
            'sample_tweet': task.info.get('sample_tweet', {}),
            'topics': task.info.get('topics')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'number': 0,
            'status': str(task.info)   # this is the exception raised
        }
    return jsonify(response)


@app.route('/', methods=['GET', 'POST'])
def index():
    # index_img=return_img_stream("/Users/xkchen/Desktop/large data stream/project/tweet_hot_topic/svm.png")
    if request.method == 'GET':
        return render_template('index.html', start_time=session.get('start_time', ''),
                               time_period=session.get('time_period', ''),
                               time_interval=session.get('time_interval', ''),
                               display_interval=session.get('display_interval', '')
                               )
    start_time = request.form['start_time']
    session['start_time'] = start_time
    start_time_datetime = datetime.strptime(start_time, '%Y-%m-%d_%H/%M')
    start_time_timestamp = (start_time_datetime - datetime(1970, 1, 1)).total_seconds() + 14400

    time_period = request.form['time_period']
    session['time_period'] = time_period

    time_interval = request.form['time_interval']
    session['time_interval'] = time_interval

    display_interval = request.form['display_interval']
    session['display_interval'] = display_interval

    # if request.form['submit'] == 'set':
    write_file = open('setting.txt', 'w')
    data_to_write = {}
    data_to_write['time'] = time.time()
    data_to_write['start_time'] = start_time_timestamp
    data_to_write['time_period'] = int(time_period)
    data_to_write['time_interval'] = int(time_interval)
    data_to_write['display_interval'] = int(display_interval)
    write_file.write(str(data_to_write))
    print 'writing setting success'

    return redirect(url_for('index'))


def return_img_stream(img_local_path):
    # get img stream
    # :param img_local_path: fullpath of img
    # :return: img stream
    import base64
    img_stream = ''
    with open(img_local_path, 'r') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream)
    return img_stream


if __name__ == '__main__':
    app.run(debug=True)
