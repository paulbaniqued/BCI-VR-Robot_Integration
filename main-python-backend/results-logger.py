"""Test prediction stream output from NeuroPype."""
import numpy as np
import pandas as pd
from time import sleep
from threading import *
import concurrent.futures
from pylsl import StreamInlet, resolve_stream
import json
import os

with open('E:/bci/session/ids.json','r') as fp:
    session_key = json.load(fp)

day = input("\n\n What session is it today? ")
session_id = session_key.get(day) + ".csv"
data_path = 'E:\\bci\\data\\csv\\'

column_names = ['trial','truth','prediction','prob_left','prob_right','score']
session_log = pd.DataFrame(columns=column_names)
trial_counter = 0
score = 0

print("looking for a Truth stream...")
truths = resolve_stream('name', 'Truth')
truths_inlet = StreamInlet(truths[0])
print("Found Truths!")

print("looking for a Prediction stream...")
predictions = resolve_stream('type', 'Prediction')
pred_inlet = StreamInlet(predictions[0])
print("Found Predictions!")

def truths_stream(truths_inlet):

    while True:
        truth_value = truths_inlet.pull_sample()
        truth_value = truth_value[0][0]
        return truth_value
    
def predictions_stream(pred_inlet):

    while True:

        sample = pred_inlet.pull_sample()
        left_prediction = sample[0][0]
        right_prediction = sample[0][1]
        return left_prediction, right_prediction

while True:

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_truths = executor.submit(truths_stream, truths_inlet)
        future_predictions = executor.submit(predictions_stream, pred_inlet)

        trial_counter += 1
    
        truth = future_truths.result()
        left, right = future_predictions.result()

        if left > right:
            prediction = 'left'
            pred_prob = left
        elif left < right:
            prediction = 'right'
            pred_prob = right
        else:
            prediction = 'equal'
            pred_prob = [left, right]

        if truth == prediction:
            score += 1

        results = pd.DataFrame([[trial_counter, truth, prediction, left, right, score]], columns=column_names)
        print("Results: ")
        print(results)

        session_log = session_log.append(results, ignore_index=True)
        print("Session log: ")
        print(session_log)

        session_log.to_csv(os.path.join(data_path,session_id), index=False)



        
