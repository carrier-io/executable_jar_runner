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
        # Optimized pattern to capture everything between 'content=' and '======'
        body_pattern = re.compile(r"content=(.*?)(?=\n=+)", re.DOTALL)
        # Updated error pattern for response body (multi-line JSON after 'body:')
        error_pattern = re.compile(
            r"(?P<timestamp>\d{2}:\d{2}:\d{2}\.\d{3}) .*? Request '(?P<request_name>.*?)' failed for user .*?: (?P<error_message>.*?)\n"
            r".*?(?P<method>GET|POST|PUT|DELETE) (?P<url>https?://[^\s]+)\n"
            r"headers:\n(?P<request_headers>(?:\t.*?\n)*)"
            r".*?status:\n\t(?P<response_code>\d+).*?"
            r".*?body:\n(?P<response_body>.*?)<<<<<<<<<<<<<<<<<<<<<<<<<",
            re.DOTALL
        )
        # Read CSV file from the last known position
        with open(self.error_log_file_path, 'r') as file:
            file.seek(self.last_position)
            new_data = file.read()
            self.last_position = file.tell()
            errors = []
            if new_data:
                # List of sensitive header names (lowercase)
                sensitive_headers = [
                    'authorization', 'proxy-authorization', 'x-api-key', 'x-auth-token', 'x-access-token',
                    'set-cookie', 'cookie', 'password', 'x-password', 'x-session-token', 'x-csrf-token',
                    'x-xsrf-token', 'x-refresh-token', 'x-secret', 'x-client-secret', 'x-client-key',
                    'x-private-key', 'x-user-token', 'x-user-secret', 'x-otp', 'x-mfa', 'x-sso-token',
                    'x-id-token', 'x-refresh-token', 'x-jwt', 'jwt', 'bearer'
                ]
                for match in error_pattern.finditer(new_data):
                    error_data = match.groupdict()

                    # Extract request parameters from URL (if any)
                    url_parts = error_data["url"].split("?")
                    request_params = url_parts[1] if len(url_parts) > 1 else None

                    # Clean up headers and hide sensitive info
                    request_headers = {}
                    for line in error_data["request_headers"].strip().split("\n"):
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k_lower = k.strip().lower()
                            v_lower = v.strip().lower()
                            # Hide if header name is sensitive or value contains 'bearer' or 'password'
                            if k_lower in sensitive_headers or any(s in v_lower for s in sensitive_headers):
                                request_headers[k.strip()] = '***'
                            else:
                                request_headers[k.strip()] = v.strip()
                    # Extract request body if present (include braces)
                    request_body = ""
                    body_match = body_pattern.search(new_data, match.start(), match.end())
                    error_key = f'{error_data["request_name"]}_{error_data["method"]}_{error_data["response_code"]}'
                    if body_match:
                        request_body = body_match.group(1).strip().replace("\t", " ").replace("\\t", " ").replace(
                            "\n", " ").replace("\\n", " ")
                    if len(request_body) > 5000:
                        request_body = request_body[:5000] + '...truncated'
                    response_body = error_data["response_body"].strip().replace("\t", " ").replace("\\t", " ").replace(
                        "\n", " ").replace("\\n", " ") if error_data.get("response_body") else ""
                    if len(response_body) > 5000:
                        response_body = response_body[:5000] + '...truncated'

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
                        "request_body": request_body,  # New field
                        "response_body":  response_body
                    })
            for each in errors:
                error_log_line = f'Error key: {each["error_key"]}\tRequest name: {each["request_name"]}\t' \
                                 f'Method: {each["method"]}\tResponse code: {each["response_code"]}\t' \
                                 f'URL: {each["url"]}\tError message: {each["error_message"]}\t' \
                                 f'Request params: {each["request_params"]}\tHeaders: {each["request_headers"]}\t' \
                                 f'Request body: {each["request_body"]}\t' \
                                 f'Response body: {each["response_body"]}\t\n'

                with open(f"/tmp/{self.args['simulation']}.log", "a") as errors_file:
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