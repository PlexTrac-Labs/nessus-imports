import argparse
from typing import List, Union, Dict, Tuple
import json
import os
import ssl
import requests
from getpass import getpass


def get_auth_header(authorization_token: str) -> Dict[str, str]:
    return {
        'Authorization': authorization_token
    }


def handle_mfa(url, token: str) -> Union[Dict[str, str], None]:
    try:
        mfa_token = getpass(prompt='Please enter your multi-factor authentication token:\n')
        mfa_response = requests.post(
            f'{url}/authenticate/mfa',
            headers=get_auth_header(
                token
            ),
            json={
                "token": mfa_token
            }
        )

        if mfa_response.status_code == 200:
            mfa_json_response = json.loads(mfa_response.text)
            if mfa_json_response.get('token') != '':
                return get_auth_header(
                    mfa_json_response.get('token')
                )
    except Exception as error:
        print(f'Error performing MFA: {error}')


def auth_request(data: Dict[str, str], url: str) -> Union[Dict[str, str], None]:
    try:
        response = requests.post(f'{url}/authenticate', json=data)

        if response.status_code == 200 and response.text != '':
            try:
                response_json = json.loads(response.text)
                if not response_json.get('mfa_enabled') and response_json.get('token') != '':
                    return get_auth_header(
                        response_json.get('token')
                    )
                else:
                    handle_mfa(
                        url,
                        response.get('token')
                    )
            except Exception as err:
                print(f'Error, malformed API response, please try again: {err}')
    except Exception as error:
        print(error)


def load_nessus_file(nessus_path: str) -> List[Tuple]:
    if not os.path.exists(nessus_path):
        raise Exception(f'Specified Nessus file {nessus_path} does not exist, please try again.')
    return [
        ('file', open(nessus_path, 'rb'))
    ]


def import_nessus_file(url: str, auth_header: str, nessus_file_data: any, client: str, report: str) -> None:
    try:
        response = requests.post(
            f'{url}/client/{client}/report/{report}/import/nessus',
            headers=auth_header,
            data={},
            files=nessus_file_data
        )

        if response.status_code == 200:
            ui = base_url.replace(':4350', '').replace('/api/v1', '')
            print(f'Import successful!')
            print(
                f'Visit your new report at: {ui}/client/{client_id}/report/{report_id}/flaws to view the results!'
            )
    except Exception as error:
        print(f'Error running nessus import: {error}')


def get_clients(url: str, auth_header: str) -> Union[Dict[str, str], None]:
    try:
        response = requests.get(
            f'{url}/client/list',
            headers=auth_header
        )

        if response.status_code == 200:
            return json.loads(response.text)
    except Exception as error:
        print(f'Error getting client list: {error}')


def setup_report(url: str, auth_header: str, client_id: str, report_name: str) -> Union[str, None]:
    create_new_report = input('Please enter your target report ID, leave blank if you want a new report:\n')

    if create_new_report != '':
        return create_new_report
    else:
        try:
            response = requests.post(
                f'{url}/client/{client_id}/report/create',
                data={
                    'name': report_name,
                    'description': f'Nessus import result: {report_name}',
                    'status': 'Open',
                    'logistics': '',
                    'template': '',
                    'start_date': '',
                    'end_date': '',
                    'fields_template': ''
                },
                headers=auth_header
            )

            if response.status_code == 200 and response.text != '':
                return json.loads(response.text).get('report_id')
        except Exception as error:
            print(f'Error creating report: {error}')


def create_client(url: str, auth_header: str) -> Union[str, None]:
    try:
        client_name = input('Please enter your new client name: \n')
        client_description = input('Please enter your client description: \n')
        client_poc = input('Please enter your client POC: \n')
        client_poc_email = input('Please enter your client POC email: \n')

        response_create_client = requests.post(
            f'{url}/client/create',
            json={
                'name': client_name,
                'description': client_description,
                'poc': client_poc,
                'poc_email': client_poc_email
            },
            headers=auth_header
        )

        if response_create_client.status_code == 200 and response_create_client.text != '':
            json_response = json.loads(response_create_client.text)
            return json_response.get('client_id')
    except Exception as error:
        print(f'Error creating client: {error}')


def setup_client(url, auth_header):
    global client_id

    try:
        clients = get_clients(url, auth_header)
        client_ids = []

        for client in clients:
            if len(client.get('data')) == 3:
                print(f'Client ID: {client.get("doc_id")[0]} name: {client.get("data")[1]}')
                client_ids.append(f"{client.get('doc_id')[0]}")

        while client_id is None:
            client_to_use = input(
                'Please enter the client ID from the list above that you are importing data to (leave blank to create)\n'
            )

            if client_to_use == '':
                client_id = create_client(url, auth_header)
            elif client_to_use in client_ids:
                client_id = client_to_use
    except Exception as error:
        print(f'Error setting up client data: {error}')

    return client_id


if __name__ == '__main__':
    try:
        hostname = input('Please enter the hostname of your PlexTrac instance (with protocol): \n')
        username = input('Please enter your PlexTrac username: \n')
        password = getpass(prompt='Password: \n')
        path_to_nessus_file = input(
            'Please provide a path to the Nessus XML export you would like to upload to PlexTrac\n'
        )
        print('file input requested')
        base_url = f'{hostname}/api/v1'
        client_id = None
        report_id = None

        auth_data = {
            'username': username,
            'password': password
        }
        print('attempting to login')
        # perform authentication
        authorization_header = auth_request(auth_data, base_url)

        # if authenticated
        if authorization_header is not None:
            print('got token, login successful')
            print('attempting client setup')
            # get client list and prompt user for the client they'd like to use
            client_id = setup_client(base_url, authorization_header)

            if client_id is not None:
                print('got client, loading nessus file')
                nessus_data = load_nessus_file(path_to_nessus_file)
                print('nessus file loaded')
                if report_id is None:
                    print('performing report setup')
                    report_id = setup_report(
                        base_url,
                        authorization_header,
                        client_id,
                        os.path.basename(path_to_nessus_file)
                    )

                if report_id is not None:
                    if nessus_data is not None:
                        print('importing data')
                        import_nessus_file(base_url, authorization_header, nessus_data, client_id, report_id)
    except Exception as e:
        print(f"Error importing data: {e}")
