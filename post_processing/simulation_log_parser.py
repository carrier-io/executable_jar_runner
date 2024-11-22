import time
import argparse
import os, shutil
from influxdb import InfluxDBClient
from traceback import format_exc
import uuid
import random


class CSVHandler:
    def __init__(self, csv_path, external_client, internal_client, args):
        self.args = args
        self.csv_path = csv_path
        self.external_client = external_client
        self.internal_client = internal_client
        self.last_position = 0  # Initial position in the file
        self.active_users = 0
        #self.uuid_list = [str(uuid.uuid4()) for _ in range(100)]
        self.uuid_list = ['5b940c55-11da-4a64-bd18-556277eb15c7', '9cb01980-fd47-4a2c-a83b-9b8c908b9f73', 'a4bdfa25-9c04-4cf8-b1f0-ccff42d99260', '14b21c0c-21fd-4ffe-a52c-b5429275a060', '3a785b8a-5dff-4112-ab30-e5c783535603', '53aad4ca-493b-4773-a6c7-01cf0def085c', '3b2d5a0d-0fdb-4dad-ac46-191a1d9a355d', '99d84586-6c22-4325-8500-57ddda1ae397', '5dbbaf7b-37cd-40de-b451-9639ff53310f', '50928c9e-2ecf-41fe-a48e-42930aa9f41b', '802bf5d0-0242-4942-91f7-5d17377a99bb', 'e8b0a5ce-9d1a-4a97-ba80-4dffa3fc0054', '1850ce92-d8b8-4692-8641-0531bf5ba2a7', 'e00e97f0-0cb6-4861-9a43-d6dc398b12fd', '7e799eb7-487d-4213-b275-3d07bba20441', 'e98eeec9-17f8-46a9-a844-d811fbab25d5', '6d00c033-599c-4bd2-9dc7-a1b79ba975a2', 'bb57b45d-05ab-420a-9f71-0ba519236474', 'affc1e5b-b84c-46b2-a626-d1bc07399640', 'b6ac4c66-d8b3-4c28-82c0-426ae50582eb', '08a823a3-55fc-45a8-bcbb-b79733789993', '3e1df465-5538-496d-b74d-d00a51c0fbb5', 'e0adfaad-0980-4349-b4df-3ee1c4fcd601', 'f2e89d60-7225-4972-900c-41516d5af32f', '102016dd-bcfd-4dcd-b87b-8e63df40e408', 'e53fbaf2-844b-465b-bf54-d8f6f1bb6411', '7ae4a059-89a3-4887-a337-578c81dfe4c8', '8a0b58a0-ba4a-43de-b883-772745a1f742', 'ec057f55-7b8e-44ee-9228-2973e74ba37a', 'be4e4c35-f112-4541-b120-8bbd326e4d27', 'ace8f0a7-e8c6-4b13-a083-0974965c58a0', 'e0902de7-37b0-462a-902e-d6f906fc5395', '936ba98a-3fda-43b7-a745-5c887f592f64', '84750d87-7425-40fd-9f19-d5880bee4de2', '2bd4fee9-d041-495a-b658-23ff1d404160', 'b0fe17b1-c809-47ba-ba8d-c0806d893b35', 'fb685fad-47b4-47f7-ad29-a9f6c20ae53b', '6b77074b-34d2-4e1b-a75f-bf21b7f261cf', '34767e0f-6f15-4f8f-ae4d-936edfc9c48d', '9cc883c1-0ac4-4518-9534-863dc6365c8b', '5f295bca-dcc2-4c62-b47b-e0eda87c4095', '9e9e3ea9-7403-4362-9e00-f60440117e3b', 'a6a5f719-af16-4a80-adcc-2fadd62a1fae', '0ea79f0e-9b79-4469-9cf6-dd00c8531e12', 'cdc3540c-3b1b-4032-8e4c-5581a2ae9aa1', '3518ada5-89a3-43b6-b126-651031e918d6', 'f072a4ea-1566-47d5-8e91-69cb36ef25a0', '14ced03f-c0dc-4a4f-92c5-d69bd8b4fb3d', '393d1608-7c0c-4a1b-8c7c-7a5125b64ec6', '41ef3809-510d-465f-bba1-a04c545ffdfb', '8e976958-cbaf-46d4-a0ae-092241f8a416', 'd8c8f961-dbc9-4acc-a14b-2c9d251b45ca', '24aec1b3-82da-4242-b211-d7b12d3c9863', 'ae15a4fc-1a1c-4507-8469-c1f82f707e96', '34d43558-21e8-4f58-89e5-dc06fc7d6fe5', '87cbf278-15eb-4882-8a79-d5a6a9b527c3', '5812e90d-e07c-40e3-8f68-77fb7232d148', 'c0911f41-47a6-40ea-b636-a50b3196984e', '7fa6b3ba-abc2-44fe-923c-d299b0cf00a6', '9735122d-1e3e-4285-bc87-db6576b0cf47', '8238b7a8-be23-43e5-8286-0b6b8a6293c6', 'c7840ef0-3961-4e12-a729-16cf198edfd2', 'f3ec7f1b-9df2-448d-8566-ba1571cf0f28', 'c89e14dc-12ca-4648-9103-66b8ad18aaf6', '1f12a964-f157-4cc4-b628-3442cfb0c9aa', '3b07bdf1-e380-4412-aa42-12a4c9489b5b', '6511bafc-67f2-4ae9-a8b1-dde33ae26d7e', 'e30db302-85b6-44ea-b8a5-330af1a8133a', '2c4fbdb1-0b2e-461c-8267-e8e4c828dd40', 'e4893a59-6f73-4eb6-b79b-5f51c36016f4', '51c9f3f3-8a80-42f6-94f6-034770633cb9', '5fb55c67-1456-4044-bd09-2da4aa3be6e0', '58dc97e3-7630-4bcf-8c44-7a5592d6b0c0', '4f600c81-f221-4522-9ec6-9111579b604a', 'fd0d583b-d0f9-4251-a5ba-65fab1d9367e', '2c61dc6b-203e-4a24-bf28-ffba22b83b97', 'e7ad00b0-57b1-4b58-8506-411694fad0d6', '8b9d7120-9977-43ea-95f0-bc9bb77a40cf', 'ece805b8-7887-476a-a6b9-6e13ff308f20', '88b82f2f-e998-4022-805b-0fd97b9735a0', '97381408-1d1e-4b50-ac89-cfef26f01d0a', '6247e4df-a048-499c-b46b-569876383cef', '65856d43-8f7e-4b9a-84cf-dd726f32971e', 'f8b1f9fe-fd51-41d0-9b84-a1773879ef81', '15dc5fc0-ed38-45a6-aa63-586826c9d9a7', '23b36329-e497-4e21-8dac-b0ebe0b1488b', '6cbf8a9a-8081-4554-ad3e-5e349e71041d', '6add5013-9445-46cc-9b6c-3662e586bf12', 'f966c52d-32f2-45cd-9360-e42b3777cfce', 'c6b1dc5c-07e3-4eba-a787-cd9bacda1da9', '151dc118-1917-4d26-9eea-7f21297ad543', '5bd7ccc8-220f-484e-b74a-a2bf7b58c521', 'd3d4b535-b2fd-4856-9f31-9e1ef975dbac', '3fd931d3-cd95-4fe6-ba5c-d8d8df6c6501', '8dd09ffa-e035-43c7-aecb-de79e89f4a51', '5daeb84e-af23-413b-ab2c-17b5e3cb07c7', '7d8bdaa8-54a2-4520-90f3-28208f870084', '515a42c3-a8fd-4f57-a325-ee5bd5ad7028', '7556faad-cd45-42c2-8731-1f069500de34', '661097db-662d-455e-bad9-0bbdd70f1b59']


    def check_new_records(self):
        # Read CSV file from the last known position
        with open(self.csv_path, 'r') as file:
            file.seek(self.last_position)
            new_data = file.readlines()
            records = []
            results = []
            user_records = []
            users = []
            if new_data:
                for each in new_data:
                    if each.startswith("USER"):
                        user_records.append(each.replace("\n", ""))
                for each in user_records:
                    try:
                        _tmp = each.split("\t")
                        if _tmp[2] == "START":
                            self.active_users += 1
                        else:
                            self.active_users -= 1
                        users.append({"time": int(_tmp[3]), "active": self.active_users})
                    except Exception as e:
                        print(e)
                        print(format_exc())

                for each in new_data:
                    if each.startswith("GROUP") or each.startswith("REQUEST"):
                        records.append(each.replace("\n", ""))
                for each in records:
                    try:
                        _tmp = each.split("\t")

                        if _tmp[0] in ["GROUP", "REQUEST"]:
                            if _tmp[0] == "GROUP":
                                response_time = int(_tmp[3]) - int(_tmp[2])
                                request_name = _tmp[1]
                                timestamp = int(_tmp[2])
                            else:
                                response_time = int(_tmp[4]) - int(_tmp[3])
                                request_name = _tmp[2]
                                timestamp = int(_tmp[3])
                            _res = {
                                "time": timestamp,
                                "simulation": self.args["simulation"],
                                "request_name": request_name,
                                "response_time": response_time,
                                "method": "TRANSACTION" if _tmp[0] == "GROUP" else "GET",
                                "status": _tmp[5],
                                "status_code": 200,
                                "user_id": random.choice(self.uuid_list),  # TODO check user_id
                                "env": self.args["env"],
                                "test_type": self.args["type"],
                                "build_id": self.args["build_id"],
                                "lg_id": self.args["lg_id"]
                            }
                            results.append(_res)
                    except Exception as e:
                        print(e)
                        print(format_exc())

                if not users:
                    users.append({"time": int(time.time() * 1000), "active": self.active_users})
                    print(users)
                print(f"Users count: {len(users)}")
                print(f"Active Users: {self.active_users}")
                print(f"Results count: {len(results)}")
                # Update the last known position
                self.last_position = file.tell()

            users_internal_points, users_external_points = [], []
            for req in users:
                users_internal_influx_record = {
                    "measurement": "users",
                    "tags": {},
                    "time": int(req["time"]) * 1000000,
                    "fields": {
                        "measurement_name": "users",
                        "active": req["active"],
                        "waiting": 0,
                        "done": 0,
                        "user_count": 0
                    }
                }
                users_internal_points.append(users_internal_influx_record)

                users_external_influx_record = {
                    "measurement": "users",
                    "tags": {
                        "test_type": self.args["type"],
                        "simulation": self.args["simulation"],
                        "build_id": self.args["build_id"],
                        "lg_id": self.args["lg_id"]
                    },
                    "time": int(req["time"]) * 1000000,
                    "fields": {
                        "measurement_name": "users",
                        "active": req["active"],
                        "waiting": 0,
                        "done": 0,
                        "user_count": 0
                    }
                }
                users_external_points.append(users_external_influx_record)


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
            self.internal_client.write_points(users_internal_points)

            # Write data to external InfluxDB
            self.external_client.write_points(external_points)
            self.external_client.write_points(users_external_points)


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
    while not os.path.exists(folder):
        time.sleep(10)  # Sleep for a specified time before checking again
    print(f"Directory '{folder}' has appeared!")
    # for filename in os.listdir(folder):
    #     file_path = os.path.join(folder, filename)
    #     try:
    #         if os.path.isfile(file_path) or os.path.islink(file_path):
    #             os.unlink(file_path)
    #         elif os.path.isdir(file_path):
    #             shutil.rmtree(file_path)
    #     except Exception as e:
    #         print('Failed to delete %s. Reason: %s' % (file_path, e))
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