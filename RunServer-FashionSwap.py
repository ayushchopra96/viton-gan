import werkzeug
import cPickle
import logging
import datetime
import time
from flask import send_file, send_from_directory
import random
import shlex
import pylibmc
import psutil
import socket
import json
from PIL import Image
import cStringIO as StringIO
import urllib
from flask import Flask, jsonify, render_template, request, make_response
from flask_cors import CORS, cross_origin
import numpy as np
import os
import sys
import json
import subprocess
import png
import requests
import cv2
from scipy import misc

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['TEMP_FOLDER'] = './tempout'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['LOC_FILE'] = 'vectors'
app.config['JSON_FOLDER'] = 'jsons'

def savePng(im,filename):
    ##########Black..Red..Green..Yellow..Blue..Pink..Cyan.
    imoutfile=open(filename,'wb')
    pngWriter=png.Writer(im.shape[1], im.shape[0],greyscale=True,bitdepth=8)
    pngWriter.write(imoutfile,np.reshape(im, (-1, im.shape[1])))
    imoutfile.close();

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

def readyDir(directory):
   if not os.path.exists(directory):
      os.makedirs(directory)
   return 0; 

def storeAppVariables():
      mc =app.mc;
      # mc["net"]=app.net;
      # mc["transformer"]=app.transformer_data
    
def loadAppVariables():
      mc = pylibmc.Client(["127.0.0.1"], binary=True,
      behaviors={"tcp_nodelay": True,
      "ketama": True});
      app.mc=mc
      # app.net=mc["net"]
      # app.transformer_data=mc["transformer"]

def initApp():
    #app.Get_All_Data=Get_All_Data()
    mc = pylibmc.Client(["127.0.0.1"], binary=True,
    behaviors={"tcp_nodelay": True,
    "ketama": True});
    app.mc=mc;
    storeAppVariables();
    print app.config['UPLOAD_FOLDER'];
    print app.config['TEMP_FOLDER'];
    #app.config['UPLOAD_FOLDER']=argv[0].rsplit(os.sep,1)[0]+os.sep+app.config['UPLOAD_FOLDER']
    #app.config['TEMP_FOLDER']  =argv[0].rsplit(os.sep,1)[0]+os.sep+app.config['TEMP_FOLDER']
    readyDir(app.config['UPLOAD_FOLDER']);
    readyDir(app.config['TEMP_FOLDER']);

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

@app.route('/')
def index():
    return render_template('cindex_fash.html', has_result=False)

def image_concat(img_paths):
	num_imgs = len(img_paths)
	to_ret_img = np.zeros((675*num_imgs,675,3)) 
	for ix in range(len(img_paths)):
		f = Image.open(img_paths[ix])
		f = misc.imresize(f,(675,675))
		f = np.array(f)
		#if f.shape[0]!=675 or f.shape[1]!=675:
			#f = np.resize(f,(675,675,3))
		to_ret_img[ix*675:(ix+1)*675,:675,:] = f 
	#indx = np.random.randint(0, num_imgs)
	#to_ret_image_path = img_paths[indx]
	path = 'tempout/'+str(np.random.randint(1,100))+'.jpg'
	Image.fromarray(np.array(to_ret_img,dtype=np.uint8)).save(path)
	#Image.fromarray(to_ret_img).save(path)
	#wld = WildSearch()
	return path

def download3(query_image,vectors_dict, INP_FILE):
	to_ret = dict()
	for ix in vectors_dict:
		to_ret[ix] = vectors_dict[ix].reshape(4096).tolist()
	matrix_path = app.config['JSON_FOLDER']+'/'+query_image.split('/')[-1].split('.')[0]+'.json'
	#print matrix_path
	return json.dumps(to_ret,indent=2)
	#with open(matrix_path,'w') as outfile:
		#json.dumps(to_ret, outfile)
	#return send_file(matrix_path, as_attachment=True,attachment_filename=INP_FILE.split('.')[0]+'.json')
	
def download_mask():
	mat_path = 'my_mask.png'
	return send_file(mat_path, mimetype='image/png')

def download2(query_image,INP_FILE):
	matrix_path = app.config['LOC_FILE']+'/'+query_image.split('/')[-1].split('.')[0]+'.npy'
	#content-Disposition: attachment; filename=matrix_path
	return send_file(matrix_path, as_attachment=True,attachment_filename=INP_FILE.split('.')[0]+'.npy')

def download(vectors_dict):
	f = vectors_dict
	response = make_response(str(f))
	response.headers["Content-Disposition"] = "attachment; filename=test.npy"
	return response
	
def generated_output(output, person, cloth):
  img_paths = [person, cloth, output]
  num_imgs = len(img_paths)
  to_ret_img = np.zeros((675*num_imgs,675,3))
  for ix in range(len(img_paths)):
    f = Image.open(img_paths[ix])
    f = misc.imresize(f,(675,675))
    f = np.array(f)

    to_ret_img[ix*675:(ix+1)*675,:675,:] = f

  path = 'tempout/'+str(np.random.randint(1,100))+'.jpg'
  Image.fromarray(np.array(to_ret_img,dtype=np.uint8)).save(path)
  #Image.fromarray(to_ret_img).save(path)
  #wld = WildSearch()
  return path

@app.route('/search', methods=['POST'])
def search():
    print "entering search.."
    #val = request.form['debug']
    #debug=False
    #if val=="Yes":
	#debug=True
    try:
        uploaded_files =  [request.files['personimage'], request.files['clothimage']]
        filenames =[]
	INP_FILE = None
	print "Search beginning"
	start = datetime.datetime.now()
        for file in uploaded_files:
           # print file
           # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                filename_ = str(datetime.datetime.now()).replace(' ', '_') + \
                            werkzeug.secure_filename(file.filename)
		INP_FILE = file.filename
                filename = os.path.join(app.config['UPLOAD_FOLDER'], filename_)
                file.save(filename)
                filenames.append(filename)
                logging.info('Saving to %s.', filename)
    except Exception as err:
        logging.info('Uploaded image open error: %s', err)
        return 'Cannot open uploaded image.'
    except:
        print "Unexpected error:", sys.exc_info()[0]
        return 'Unknow Error'
    person_image = filenames[0]
    cloth_image = filenames[1]
    subprocess.call(['./run_smartfit.sh', person_image, cloth_image])
    output_path = './output/output.png'
    generated_output_path = generated_output(output_path, person_image, cloth_image)
    return send_file(generated_output_path, mimetype='image/jpeg')

@app.before_request
def before_request():
    loadAppVariables()

@app.teardown_request
def teardown_request(exception):
    storeAppVariables()


if __name__ == '__main__':
    np.set_printoptions(linewidth=1200)
    np.set_printoptions(precision=2)
    np.set_printoptions(suppress=True)
    logging.getLogger().setLevel(logging.INFO)
    initApp();    
#initApp(sys.argv);
    ipaddr=[(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    app.run(debug=False,host=ipaddr,port=9001)
