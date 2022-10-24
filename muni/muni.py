import requests
import pprint
import json
import os
from time_functions import get_time_difference
from led_matrix import output
import time
from gpiozero import Button
from signal import pause

### Stop ID Refernce: 7th St = "15539" 
###                   8th St = "15540"

# Button assignments
green_button = Button(2, hold_time=2)
blue_button = Button(22)
yellow_button = Button(5)
red_button = Button(26)


tokens = [
    "b6c22a4f-6f67-4313-b2db-65b391da6d0b",
    "74f5ca83-8ed8-45ad-9073-41249bac27c5",
    "2078a320-7c20-41d7-bf1d-4764fae72371",
    "a0078d20-190e-4b7f-a17e-a13659aa8840",
    "363a0459-def9-4b2f-a8fe-0f75feeadec8",
    "d62c17a9-2263-4cb7-ba2e-53975596dc2f"
]
tokens_index = 0

def simple_message(message):
    output(4, -90, 2, False, message)

def increment_index_in_array(index, array):
    if index == len(array) -1:
        print("index at 0")
        return 0
    else: 
        return index + 1

def get_bus_data(stop_id):
    url = f"https://api.511.org/transit/StopMonitoring?api_key={tokens[tokens_index]}&stopCode={stop_id}&agency=SF&Format=json"
    payload={}
    headers = {
    'Cookie': 'AWSELB=253BFF17149287196F6405573CBD843136012AF257BB1A91CC7DDE2456CF5B26B58E5C3D84C7EA58D0E8FF6B18600BD37E3B0D7E1F0E335CC2F550D9B27B9BD6DA4E75B97F',
    'content-type': 'application/json'
    }
    response = requests.get(url, headers=headers, data=payload)
    # pprint.pprint(response.text, indent = 2)
    # print("response type: ", type(response.content))
    return response


def display_muni_data(stop_id):
  
    response = get_bus_data(stop_id)
    print("Stop ID: ", stop_id)
    if "The allowed number of requests" in response.text:
        print("RESPONSE TEXT: ", response.text)
        print('token switch')
        tokens_index = increment_index_in_array(tokens_index, tokens)
    else:

        ### This API is creating an error and needs to be decode. Explanation on website below. 
        ### https://speedysense.com/python-fix-json-loads-unexpected-utf-8-bom-error/
        
        decoded_data = response.text.encode().decode('utf-8-sig')
        data = json.loads(decoded_data)

        #########################################################
        ###  -------- SECTION START - FILE READING & WRITING --------
        ### reference link for reading & writing: https://www.geeksforgeeks.org/reading-and-writing-json-to-a-file-in-python/
        ### reference link for  function: https://note.nkmk.me/en/python-os-path-getsize/

        # # ### utility function for reading file length
        # def get_number_of_files(path='.'):
        #   total = 0
        #   with os.scandir(path) as it:
        #     for entry in it:
        #         total += 1
        #   return total

        # ### Serializing json
        # json_object = json.dumps(data, indent=4)
        
        # ### Get the length of the folder for adding a number to the file name
        # folder_length = get_number_of_files("json_examples")

        # ### Writing the file
        # with open(F"json_examples/example_{folder_length}.json", "w") as outfile:
        #     outfile.write(json_object)

        # ### Reading the file
        # # Opening JSON file
        # with open('json_examples/no_bus_example.json', 'r') as openfile:
        
        #     # Reading from json file
        #     example_json = json.load(openfile)


        ###  -------- SECTION END - FILE READING & WRITING -------- 
        #########################################################

        #########################################################
        ###  -------- SECTION START - TRANSFORMING DATA --------
        ##### Add error handling - spefically when looking for nested object that might not be ther - this API wonky 

        ### Uncomment below to test an error json 
        # nested_data = example_json["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]

        nested_data = data["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]


        ### check that there is a bus schedule returned
        if not nested_data: 
            # print("No Bus Schedule Found")
            if stop_id == "15539":
                no_bus_txt = "No update on next 14 at 7th St"
            else:
                no_bus_txt = "No update on next 14R at 8th St"
            output(4, -90, 2, False, no_bus_txt)
        else:
            arrivals = []

            for item in nested_data:
                if stop_id == "15540" and item["MonitoredVehicleJourney"]["LineRef"] != "14":
                    print("condition check: ", item["MonitoredVehicleJourney"]["LineRef"])
                    arrivals.append(item["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedArrivalTime"])
                    bus_number = item["MonitoredVehicleJourney"]["LineRef"]
                    direction = item["MonitoredVehicleJourney"]["DirectionRef"]
                    bus_stop = item["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointName"]
                elif stop_id == "15539":
                    arrivals.append(item["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedArrivalTime"])
                    bus_number = item["MonitoredVehicleJourney"]["LineRef"]
                    direction = item["MonitoredVehicleJourney"]["DirectionRef"]
                    bus_stop = item["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointName"]

            arrival_times = []
            for i in arrivals:
                arrival_times.append(get_time_difference(i))

            pprint.pprint(arrival_times)

            formatted_arrival_times = ""

            for i in range(len(arrival_times)):
                if len(arrival_times) > 1 and i != len(arrival_times) -1:
                    add_and = " & "
                else:
                    add_and = ""
                if arrival_times[i] == 1: 
                    add_s = ""
                else:
                    add_s = "s" 
                formatted_arrival_times += f"{str(arrival_times[i])} minute{add_s}{add_and}"

            if len(arrival_times) > 0:
                led_txt = f"Next {bus_number} in {formatted_arrival_times} at {bus_stop[13:]}"
                output(4, -90, 2, False, led_txt)
            elif len(arrival_times) == 0 and stop_id == "15540":
                print("Second condition check for 8th St")
                output(4, -90, 2, False, "No update on next 14R at 8th St")

            ###  -------- SECTION END - TRANSFORMING DATA --------
            #########################################################

def stream(loops):
    loop_count = 0
    stop_ids = ["15539", "15540"]
    for _ in range(loops):
        print("Loop Count: ", loop_count)
        for stop_id in stop_ids:
            display_muni_data(stop_id)
        loop_count += 1


def single_stream(stop_id):
    if not green_button.was_held:
        display_muni_data(stop_id)
    green_button.was_held = False
  

green_button.when_released = lambda: display_muni_data("15539")
blue_button.when_released = lambda: display_muni_data("15540")
yellow_button.when_pressed = lambda: stream(20)
red_button.when_pressed = lambda: simple_message("Te Amo Patricia")

pause()