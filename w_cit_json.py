import os
import argparse
import json

def extract_frame_number(file_name):
    return int(file_name.split(".")[-2])

def generate_json(data_folder):
    file_names = [file for file in os.listdir(data_folder) if file.endswith(".vtr")]
    sorted_file_names = sorted(file_names, key=extract_frame_number)

    json_content = {
        "files": sorted_file_names,
        "reader_properties": {
            "CellArrayStatus": ["temperature", "velocity"]
        },
        "fields": [
		    { "text": "temperature", "value": 0, "location": "POINTS", "range": [0, 1] },
		    { "text": "velocity", "value": 1, "location": "POINTS" , "range": [0,0]}
        ]
    }

    output_file_name = "citcomcu.json"
    with open(os.path.join(data_folder, output_file_name) , "w") as f:
        json.dump(json_content, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate JSON configuration file")
    parser.add_argument("--data", required=True, help="Path to data folder")
    args = parser.parse_args()

    generate_json(args.data)

