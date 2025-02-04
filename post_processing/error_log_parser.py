import time
import argparse
import os
import re


class ErrorLogHandler:
    def __init__(self, error_log_file_path, args):
        self.args = args
        self.error_log_file_path = error_log_file_path
        self.last_position = 0  # Initial position in the file

    def check_new_records(self):
        error_pattern = re.compile(
            r"(?P<timestamp>\d{2}:\d{2}:\d{2}\.\d{3}) .*? Request '(?P<request_name>.*?)' failed for user .*?: (?P<error_message>.*?)\n"
            r".*?(?P<method>GET|POST|PUT|DELETE) (?P<url>https?://[^\s]+)\n"
            r"headers:\n(?P<request_headers>(?:\t.*?\n)*)"
            r".*?status:\n\t(?P<response_code>\d+).*?"
            r"body:\n(?P<response_body>.*?)\n<<<<<<<<<<<<<<<<<<<<<<<<<",
            re.DOTALL
        )
        # Read CSV file from the last known position
        with open(self.error_log_file_path, 'r') as file:
            file.seek(self.last_position)
            new_data = file.read()
            self.last_position = file.tell()
            errors = []
            if new_data:
                for match in error_pattern.finditer(new_data):
                    error_data = match.groupdict()

                    # Extract request parameters from URL (if any)
                    url_parts = error_data["url"].split("?")
                    request_params = url_parts[1] if len(url_parts) > 1 else None

                    # Clean up headers
                    request_headers = {
                        line.split(":")[0].strip(): line.split(":")[1].strip()
                        for line in error_data["request_headers"].strip().split("\n")
                        if ":" in line
                    }
                    error_key = f'{error_data["request_name"]}_{error_data["method"]}_{error_data["response_code"]}'
                    # Store formatted result
                    errors.append({
                        "error_key": error_key,
                        "request_name": error_data["request_name"],
                        "method": error_data["method"],
                        "response_code": error_data["response_code"],
                        "url": error_data["url"],
                        "error_message": error_data["error_message"],
                        "request_params": request_params,
                        "request_headers": request_headers,
                        "response_body": error_data["response_body"].strip().replace("\"", "").replace("\'", "").replace("'", "")
                    })
            for each in errors:
                error_log_line = f'Error key: {each["error_key"]}\tRequest name: {each["request_name"]}\t' \
                                 f'Method: {each["method"]}\tResponse code: {each["response_code"]}\t' \
                                 f'URL: {each["url"]}\tError message: {each["error_message"]}\t' \
                                 f'Request params: {each["request_params"]}\tHeaders: {each["request_headers"]}\t' \
                                 f'Response body: {each["response_body"]}\t\n'
                with open(f"/tmp/{args['simulation']}.log", "a") as errors_file:
                    errors_file.write(error_log_line)


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
    args = get_args()
    target_file = 'simulation-errors.log'
    error_log_file_path = ""
    while True:
        for folder_path, _, files in os.walk(folder):
            if target_file in files:
                error_log_file_path = os.path.join(folder_path, target_file)
                print(f"The file at '{error_log_file_path}' exists. Continue with your script.")
        if error_log_file_path:
            break
        print(f"The file '{target_file}' does not exist. Waiting for it to appear...")
        time.sleep(5)


    handler = ErrorLogHandler(error_log_file_path, args)
    while True:
        time.sleep(10)
        handler.check_new_records()