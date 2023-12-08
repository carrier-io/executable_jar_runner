import time
import argparse
import os, shutil
from influxdb import InfluxDBClient


class CSVHandler:
    def __init__(self, csv_path, external_client, internal_client, args):
        self.args = args
        self.csv_path = csv_path
        self.external_client = external_client
        self.internal_client = internal_client
        self.last_position = 0  # Initial position in the file


    def check_new_records(self):
        # Read CSV file from the last known position
        with open(self.csv_path, 'r') as file:
            file.seek(self.last_position)
            new_data = file.readlines()
            records = []
            results = []
            if new_data:
                for each in new_data:
                    if each.startswith("GROUP"):
                        records.append(each.replace("\n", ""))
                for each in records:
                    try:
                        _tmp = each.split("\t")
                        if _tmp[0] == "GROUP":
                            _res = {
                                "time": int(_tmp[2]),
                                "simulation": self.args["simulation"],
                                "request_name": _tmp[1],
                                "response_time": int(_tmp[3]) - int(_tmp[2]),
                                "method": "TRANSACTION",
                                "status": _tmp[5],
                                "status_code": 200,
                                "user_id": "1",  # TODO check user_id
                                "env": self.args["env"],
                                "test_type": self.args["type"],
                                "build_id": self.args["build_id"],
                                "lg_id": self.args["lg_id"]
                            }
                            results.append(_res)
                    except Exception as e:
                        print(e)

                print(f"Results count: {len(results)}")
                # Update the last known position
                self.last_position = file.tell()

            internal_points, external_points = [], []
            for req in results:
                internal_influx_record = {
                    "measurement": self.args["simulation"],
                    "tags": {
                        "request_name": req['request_name'],
                        "user_id": req['user_id']
                    },
                    "time": int(req["time"]) * 1000000,
                    "fields": {
                        "simulation": req['simulation'],
                        "method": req['method'],
                        "response_time": int(req["response_time"]),
                        "status": req["status"],
                        "status_code": req["status_code"]
                    }
                }
                internal_points.append(internal_influx_record)
                external_influx_record = {
                    "measurement": self.args["simulation"],
                    "tags": {
                        "env": req['env'],
                        "test_type": req['test_type'],
                        "build_id": req['build_id'],
                        "request_name": req['request_name'],
                        "method": req['method'],
                        "lg_id": req['lg_id'],
                        "user_id": req['user_id']
                    },
                    "time": int(req["time"]) * 1000000,
                    "fields": {
                        "simulation": req['simulation'],
                        "response_time": int(req["response_time"]),
                        "status": req["status"],
                        "status_code": req["status_code"]
                    }
                }
                external_points.append(external_influx_record)

            # Write data to internal InfluxDB
            self.internal_client.write_points(internal_points)

            # Write data to external InfluxDB
            self.external_client.write_points(external_points)


def get_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-t", "--type", help="Test type.")
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)
    parser.add_argument("-b", "--build_id", help="build ID", default=None)
    parser.add_argument("-en", "--env", help="Test type.", default=None)
    parser.add_argument("-i", "--influx_host", help='InfluxDB host or IP', default=None)
    parser.add_argument("-p", "--influx_port", help='InfluxDB port', default=8086)
    parser.add_argument("-iu", "--influx_user", help='InfluxDB user', default="")
    parser.add_argument("-ip", "--influx_password", help='InfluxDB password', default="")
    parser.add_argument("-idb", "--influx_db", help='Test results InfluxDB', default="gatling")
    parser.add_argument("-l", "--lg_id", help='Load generator ID', default=None)
    return vars(parser.parse_args())

if __name__ == '__main__':
    folder = "/opt/gatling/target/gatling"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    args = get_args()
    target_file = 'simulation.log'
    csv_file_path = ""
    while True:
        for folder_path, _, files in os.walk(folder):
            if target_file in files:
                csv_file_path = os.path.join(folder_path, target_file)
                print(f"The file at '{csv_file_path}' exists. Continue with your script.")
        if csv_file_path:
            break
        print(f"The file '{target_file}' does not exist. Waiting for it to appear...")
        time.sleep(5)

    # Connect to InfluxDB
    external_client = InfluxDBClient(args["influx_host"], args["influx_port"], args["influx_user"],
                                     args["influx_password"], args["influx_db"])

    internal_client = InfluxDBClient("localhost", "8086", "", "", "local")

    handler = CSVHandler(csv_file_path, external_client, internal_client, args)
    while True:
        time.sleep(10)
        handler.check_new_records()
