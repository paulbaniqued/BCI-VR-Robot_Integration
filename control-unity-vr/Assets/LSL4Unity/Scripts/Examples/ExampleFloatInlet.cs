﻿using UnityEngine;
using System;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Assets.LSL4Unity.Scripts.AbstractInlets;

namespace Assets.LSL4Unity.Scripts.Examples
{
    /// <summary>
    /// Just an example implementation for a Inlet recieving float values
    /// </summary>
    public class ExampleFloatInlet : AFloatInlet
    {
        public Animator HandLeft;

        float trialTime = 4;

        public string lastSample = String.Empty;

        protected override void Process(float[] newSample, double timeStamp)
        {
            // just as an example, make a string out of all channel values of this sample
            lastSample = string.Join(" ", newSample.Select(c => c.ToString()).ToArray());

            //Debug.Log(newSample[0]);
            float cue = newSample[0];

            //Vector3 lift = new Vector3(0, 0.2f + emg, 0);
            //gameObject.transform.position = lift;

            if (cue == 3.0)
            {
                Debug.Log("TRIGGER LEFT");
                Debug.Log(cue);
                HandLeft.SetTrigger("Grasp");
                StartCoroutine(ResetHands());

            }
            else if(cue == 4.0)
            {
                Debug.Log("TRIGGER RIGHT");
                Debug.Log(cue);
            }

            IEnumerator ResetHands()
            {
                yield return new WaitForSeconds(trialTime);
                HandLeft.SetTrigger("Idle");
            }   


        }
    }
}