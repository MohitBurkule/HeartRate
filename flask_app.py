
# A very simple Flask Hello World app for you to get started with...

from flask import Flask,request,render_template
import json
import heartpy  as hp
import matplotlib.pyplot as plt
import hrvanalysis as hrv
import io
import base64
import datetime
import numpy as np
import scipy
import sys,os
import csv
import time

app = Flask(__name__)
def plt_to_src():
    s = io.BytesIO()
    plt.savefig(s, format='png', bbox_inches="tight")
    plt.close()
    return base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")

def pie_to_bar(normalized_ff_dist):
    plt.rcParams["figure.figsize"] = (8,8)
    plt.ylim(0, 10)
    plt.yticks([i/2 for i in range(0, 21,1)])
    plt.grid(linestyle='--', linewidth='0.5', color='black',)
    for i in range(0, 10):
        c=None
        a=0.2
        if(i<1):
          c="yellow"
        elif(i<5):
          c="green"
        else:
          c="red"
        if(2<=i<4 or i>=7):
          a=0.4
        plt.axhspan(i, i+1, facecolor=c, alpha=a)
    plt.bar(["V","P","K"],normalized_ff_dist,color=["yellow","red","blue"],edgecolor="black",width=0.5)
    for index, value in enumerate(["Vatt","Pitta","Kafa"]):
        plt.text(index-0.1, normalized_ff_dist[index]+0.1, str(round(normalized_ff_dist[index],3)),fontsize=15)
    plt.title("Vatt , Pitta , Kafa Scores  ")
    plt.show()

def store(data,mt,sr,ff=None,err=None):
    fields=[str(data),str(mt),str(sr),str(ff),str(err),str(time.time())]
    f=open("data.csv","a+")
    f.write(';'.join(fields)+"\n")
    f.flush()
    f.close()

@app.route('/', methods = ['POST','GET'])
def hello_world():
    if request.method == 'POST':
        hdata = request.form.get('hdata')
        dataplt=None
        pie=None
        bar=None
        sampling_rate=None
        measure_length=None
        normalized_ff_dist=None
        #return hdata
        try:
            hdata=json.loads(hdata)
            data=np.array(hdata['bright'])[120:]
            datetims=np.array(hdata['time'])[120:]
            measure_length=(datetims[-1]-datetims[0])/60000

            data=scipy.signal.detrend(data)
            sampling_rate=hp.get_samplerate_mstimer(datetims)
            #smooth and scale
            data=hp.scale_data(data)
            data=hp.smooth_signal(data,sampling_rate,window_length=30,polyorder=3)


            plt.rcParams["figure.figsize"] = (10,5)
            plt.title("Heart Data - Raw ")
            plt.plot(range(0,len(data)),data)
            dataplt=plt_to_src()

            working_data, measures = hp.process(data, sampling_rate,freq_method='fft',calc_freq=True)
            hp.plotter(working_data, measures,moving_average=True,show=False)
            peak_detection=plt_to_src()

            ff_dist=hrv.get_frequency_domain_features(working_data["RR_list"],sampling_frequency=sampling_rate,method="lomb")
            normalized_ff_dist=[i/ff_dist["total_power"]*10 for i in [ff_dist["vlf"],ff_dist["lf"],ff_dist["hf"]]]
            plt.pie(normalized_ff_dist,labels=["Very low ","Low ","High"])
            plt.title("Frequency distribution ")
            plt.show()
            pie=plt_to_src()

            pie_to_bar(normalized_ff_dist)

            bar=plt_to_src()
            store(hdata,measure_length,sampling_rate,ff=normalized_ff_dist,err=None)
        except Exception as e :
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            e=str(exc_type)+str( fname) + str(exc_tb.tb_lineno)

            store(hdata,measure_length,sampling_rate,ff=normalized_ff_dist,err=str(e))

            return render_template("main.html",dataplt = dataplt,error=str(e),sampling_rate=sampling_rate,measure_length=measure_length)

        return render_template("main.html",dataplt=dataplt,peak_detection_graph = peak_detection,pie=pie,bar=bar,sampling_rate=sampling_rate,measure_length=measure_length)

    return 'No data recieved!'

