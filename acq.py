"""Background EEG Acquisition Handler and ERD/ERS processor
Saves as 3D array (no_timesteps x no_channels x no_trials)
Working as of 10-01-2020"""

from pylsl import StreamInlet, resolve_stream, StreamInfo, StreamOutlet
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt, sosfreqz, filtfilt
import numpy as np
import mne
import sys
import time

# LSL Outlet for Markers
info = StreamInfo('MyStimulatorStream', 'Stimulator', 1, 100, 'string', 'myuidw43537')
outlet = StreamOutlet(info)


""" SETTINGS """

startup_duration = 5
baseline_duration = 3.5
cue_duration = 6.5
rest_duration = 2.5
sampling_duration = baseline_duration + cue_duration

# Sample rate and desired cutoff frequencies (in Hz).
fs = 500.0
sampling_frequency = fs

no_trials = 80
no_channels = 8
padding_samples = 250
actual_baseline = baseline_duration - int(padding_samples/fs)
no_rawtimesteps_i = int(sampling_frequency*sampling_duration + padding_samples) # 5250 (-250 after filter)
no_rawtimesteps = int(sampling_frequency*sampling_duration)
no_newtimesteps = 100


""" FUNCTIONS """

# Create Array for Channels

def empty_channels():

    C3 = np.array([])
    C4 = np.array([])
    FC5 = np.array([])
    FC6 = np.array([])
    C1 = np.array([])
    C2 = np.array([])
    CP5 = np.array([])
    CP6 = np.array([])
    return C3, C4, FC5, FC6, C1, C2, CP5, CP6

# Set Dimensions for Data

def data_structure(no_trials, no_channels, no_newtimesteps):
    ds_eeg = np.ndarray(shape=(no_trials, no_channels, no_newtimesteps), dtype=float)
    return ds_eeg

# Surface Laplacian

def surface_laplacian(ch1, ch2, ch3, ch4):
    oc_x = 4*ch1 - 1*ch2 - 1*ch3 - 1*ch4
    return oc_x 

# Bandpass Filter

def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band', analog = False)
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=4):
    #nyq = 0.5 * fs
    #low = lowcut / nyq
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def zero_order_butterworth(data, order, fs, lowcut, highcut):
    x = np.empty(data.shape)
    x = butter_bandpass_filter(data, lowcut, highcut, fs, order=4)
    return x

# Spectral Bandpower

def spectral_bandpower(data):
    # Should add log(1 + x)?
    return np.square(data)

# Moving Average

def moving_average(data, sampling_frequency, no_rawtimesteps, no_newtimesteps):
    ave_duration = 1*sampling_frequency
    ave_interval = 0.1*sampling_frequency
    
    ave_point = round(ave_duration*0.5)
       
    eeg_ave = np.ndarray([no_channels,no_newtimesteps])
    ave_counter = 0
    
    for i in range(no_newtimesteps):
        ave_start = round(ave_point - ave_duration*(0.5))
        ave_end = round(ave_point + ave_duration*(0.5))
        epoch = data[:, ave_start:ave_end]
        get_ave = np.ndarray.tolist(epoch.mean(axis=1))
        eeg_ave[:,ave_counter] = get_ave
        ave_point = round(ave_point + ave_interval)
        ave_counter = ave_counter + 1

    print("eeg average")
    print(eeg_ave)
    return eeg_ave

# Baseline Correction

def basecorr(data, actual_baseline, no_channels, no_newtimesteps):
    baseline = data[:,0:int(actual_baseline*10)]
    baseline_ave = baseline.mean(axis=1)
    channel_base = 0
    eeg_basecorr = np.ndarray(shape=(no_channels, no_newtimesteps), dtype=float)
    print(baseline_ave)

    for channel in range(no_channels):
        eeg_basecorr[channel_base,:] = data[channel_base,:] - baseline_ave[channel_base]
        channel_base = channel_base + 1
    
    return eeg_basecorr, baseline_ave

# ERD/ERS Relative Power

def erds(data, baseline_ave, no_channels, no_newtimesteps):
    channel_base = 0
    eeg_erds = np.ndarray(shape=(no_channels, no_newtimesteps), dtype=float)

    for channel in range(no_channels):
        eeg_erds[channel_base,:] = (data[channel_base,:]/baseline_ave[channel_base])*100
        channel_base = channel_base + 1

    return eeg_erds


""" MAIN PROCESS PIPELINE """
print("starting main process pipeline...")
time.sleep(15)

outlet.push_sample(['100']) # Create empty channels, set data structure
C3, C4, FC5, FC6, C1, C2, CP5, CP6 = empty_channels()
trial_count = 0
ds_eeg = data_structure(no_trials, no_channels, no_newtimesteps)
time.sleep(2.5)

while True:

    try:

        # Resolve an EEG stream on the lab network
        print("looking for EEG and marker streams...")
        outlet.push_sample(['200']) #Connect to LSL
        streams = resolve_stream('type', 'EEG')
        streams2 = resolve_stream('type', 'Markers')
            
        # Create a new inlet to read from the stream
        inlet = StreamInlet(streams[0]) #EEG
        get_ready = StreamInlet(streams2[0]) #marker
        print("Found EEG and marker streams...")
        time.sleep(2.5)
        outlet.push_sample(['300']) # Send signal to start playing

        while True:

            now_ready = get_ready.pull_sample()[0][0]

            if now_ready == "0":
                print("Now ready!!!!")

            elif now_ready == "2":
                print("sampling EEG... ")
                for i in range(6250-1): # 1750 N (3.5s) baseline, 3250 N (6.5s) trial, 1250 N (2.5s) rest for a total of 6250
                    sample, timestamp = inlet.pull_sample()
                    C3 = np.append(C3, sample[0])
                    C4 = np.append(C4, sample[1])
                    FC5 = np.append(FC5, sample[2])
                    FC6 = np.append(FC6, sample[3])
                    C1 = np.append(C1, sample[4])
                    C2 = np.append(C2, sample[5])
                    CP5 = np.append(CP5, sample[6])
                    CP6 = np.append(CP6, sample[7])
                    eeg_raw = np.array([C3, C4, FC5, FC6, C1, C2, CP5, CP6])

                print("sampling ended...")

            elif now_ready == "5":
                
                # Get padded samples for baseline and cue only, remove padding after filter
                eeg_rawtrials = eeg_raw[:,0:no_rawtimesteps_i]
                print(np.shape(eeg_rawtrials))

                # Plotting Raw
                #plt.ion() # generate plots per trial (Interactive mode)
                #plt.show()
                fig = plt.figure(trial_count+1)
                ax1 = fig.add_subplot(231)
                ax2 = fig.add_subplot(232)
                ax3 = fig.add_subplot(233)
                ax4 = fig.add_subplot(212)

                x_point1 = np.arange(no_rawtimesteps_i)
                ax1.plot(x_point1, eeg_rawtrials[0,:])
                ax1.plot(x_point1, eeg_rawtrials[1,:])
                ax1.plot(x_point1, eeg_rawtrials[2,:])
                ax1.plot(x_point1, eeg_rawtrials[3,:])
                ax1.plot(x_point1, eeg_rawtrials[4,:])
                ax1.plot(x_point1, eeg_rawtrials[5,:])
                ax1.plot(x_point1, eeg_rawtrials[6,:])
                ax1.plot(x_point1, eeg_rawtrials[7,:])

                # Bandpass Filter to Mu (500Hz, 8-12Hz)
                lowcut = 8.5
                highcut = 11.5

                eeg_filtered = zero_order_butterworth(eeg_rawtrials, 4, fs, lowcut, highcut)
                print(eeg_filtered)
                print(np.shape(eeg_filtered))


                # Plotting Filtered (USE TO COMPARE PADDING)
                #f, ax = plt.subplots()
                #x_point = np.arange(no_rawtimesteps_i)
                #ax.plot(x_point, eeg_filtered[0,:])
                #ax.plot(x_point, eeg_filtered[1,:])
                #ax.plot(x_point, eeg_filtered[2,:])
                #ax.plot(x_point, eeg_filtered[3,:])
                #ax.plot(x_point, eeg_filtered[4,:])
                #ax.plot(x_point, eeg_filtered[5,:])
                #ax.plot(x_point, eeg_filtered[6,:])
                #ax.plot(x_point, eeg_filtered[7,:])
                #plt.show()

                eeg_filtered = eeg_filtered[:,padding_samples:no_rawtimesteps_i]
                print(eeg_filtered)
                print(np.shape(eeg_filtered))

                # Plotting Filtered
                x_point2 = np.arange(no_rawtimesteps)
                ax2.plot(x_point2, eeg_filtered[0,:])
                ax2.plot(x_point2, eeg_filtered[1,:])
                ax2.plot(x_point2, eeg_filtered[2,:])
                ax2.plot(x_point2, eeg_filtered[3,:])
                ax2.plot(x_point2, eeg_filtered[4,:])
                ax2.plot(x_point2, eeg_filtered[5,:])
                ax2.plot(x_point2, eeg_filtered[6,:])
                ax2.plot(x_point2, eeg_filtered[7,:])

                # Get Mu Power
                eeg_powered = spectral_bandpower(eeg_filtered)
                print("Mu power: ")
                print(eeg_powered)

                # Plotting Powered
                x_point3 = np.arange(no_rawtimesteps)
                ax3.plot(x_point3, eeg_powered[0,:])
                ax3.plot(x_point3, eeg_powered[1,:])
                ax3.plot(x_point3, eeg_powered[2,:])
                ax3.plot(x_point3, eeg_powered[3,:])
                ax3.plot(x_point3, eeg_powered[4,:])
                ax3.plot(x_point3, eeg_powered[5,:])
                ax3.plot(x_point3, eeg_powered[6,:])
                ax3.plot(x_point3, eeg_powered[7,:])

                # Averaging Over Time
                eeg_ave = moving_average(eeg_powered, sampling_frequency, no_rawtimesteps, no_newtimesteps)
                print("Averaging over time: ")
                print(eeg_ave)

                # Baseline Correction
                eeg_basecorr, baseline_ave = basecorr(eeg_ave, actual_baseline, no_channels, no_newtimesteps)
                print("EEG Baseline-corrected: ")
                print(eeg_basecorr)

                # ERD / ERS percent change
                eeg_erds = erds(eeg_basecorr, baseline_ave, no_channels, no_newtimesteps)
                print("ERD / ERS Percent Change: ")
                print(eeg_erds)
                print(np.shape(eeg_erds))

                # Plotting
                x_point4 = np.arange(no_newtimesteps)
                ax4.plot(x_point4, eeg_erds[0,:])
                ax4.plot(x_point4, eeg_erds[1,:])
                ax4.plot(x_point4, eeg_erds[2,:])
                ax4.plot(x_point4, eeg_erds[3,:])
                ax4.plot(x_point4, eeg_erds[4,:])
                ax4.plot(x_point4, eeg_erds[5,:])
                ax4.plot(x_point4, eeg_erds[6,:])
                ax4.plot(x_point4, eeg_erds[7,:])
                #plt.show()
                #plt.draw()
                #plt.pause(0.001)


                # Compile Data
                ds_eeg[trial_count,:,:] = eeg_erds[:,:]

                # Reset
                C3, C4, FC5, FC6, C1, C2, CP5, CP6 = empty_channels()
                print("C3 bin empty?: ", C3, C3.shape)
                trial_count = trial_count + 1

            elif now_ready == "6":
                print("end of trials...")
                print(ds_eeg)
                print(np.shape(ds_eeg))

                # Save as CSV
                np.save("training_data.npy", ds_eeg)
                
                sys.exit()
    
    except KeyboardInterrupt:
        print("Closing program...")
    
    finally:
        sys.exit()

