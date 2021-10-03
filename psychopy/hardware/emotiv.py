############
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#############

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 14:03:17 2017

@author: bill.king
"""

import os
import json
import threading
import datetime
from sys import platform
import websocket
import ssl
import time
from pathlib import Path
import logging  # NB this is the Python built-in logging not PsychoPy's
import pandas as pd
from psychopy import prefs

# Set up logging for websockets library

logger = logging.getLogger('test_logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(Path(prefs.paths['userPrefsDir'])/'cortex.log')
logger.addHandler(fh)


MS_SEC_THRESHOLD = 1E+10  # if timestamp is greater than this it is in ms
EEG_ON = os.environ.get('CORTEX_DATA', False)


class CortexApiException(Exception):
    pass


class CortexTimingException(Exception):
    pass


class CortexNoHeadsetException(Exception):
    pass


class Cortex(object):
    if os.getenv('CORTEX_DEBUG', False):
        CORTEX_URL = "wss://localhost:7070"
    else:
        CORTEX_URL = "wss://localhost:6868"

    def __init__(self, client_id_file=None, subject=None):
        
        if platform == "linux" or platform == "linux2":
            raise NotImplementedError('Linux not yet supported')

        self.client_id = None
        self.client_secret = None
        client_id, client_secret = self.parse_client_id_file()
        self.set_client_id_and_secret(client_id, client_secret)
        self.id_sequence = 0
        self.session_id = None
        self.marker_dict = {}
        self.waiting_for_id = None
        self.websocket = None
        self.auth_token = None
        logger.debug("Connection initializing")
        self.init_connection()
        logger.debug("Connection initialized")

        self.get_user_login()
        self.get_cortex_info()
        self.has_access_right()
        self.tt0 = time.time() - time.perf_counter()
        self.request_access()
        self.authorize()
        self.get_license_info()
        self.headsets = []
        self.query_headsets()
        if len(self.headsets) > 0:
            if len(self.headsets) > 1:
                logger.warning(
                    "Currently Psychopy only supports a single headset")
                logger.warning("Connecting to the first headset found")
            time_str = datetime.datetime.now().isoformat()
            self.create_session(activate=True,
                                headset_id=self.headsets[0])
            self.create_record(title=f"Psychopy_{subject}_{time_str}".replace(":",""))
        else:
            logger.error("Not able to find a connected headset")
            raise CortexNoHeadsetException("Unable to find Emotiv headset")
        # EEG data 
        if EEG_ON:
            self.timestamps = []
            self.data = []
            self.marker_buffer = []
            self.columns = None
            self.marker_idx = None
            self.subscribe(['eeg'])

        self.running = False
        self.listen_ws = self.start_listening()

    def send_command(self, method, auth=True, **kwargs):
        self.send_wait_command(method, auth, wait=False, **kwargs)

    def send_wait_command(self, method, auth=True, callback=None,
                          wait=True, **kwargs):
        """
        Send a command to cortex.

        Parameters:
            method: the cortex method to call as a string
            auth: boolean to indicate whether or not authentication is
                required for this method (may generate an additional call to
                authorize())
            callback: function to be called with the response data; defaults
                to returning the response data
            wait: flag whether to get response or send and forget
            **kwargs: all other keyword arguments become parameters in the
                request to cortex.
        Returns: response as dictionary if wait is True
        """
        if not self.websocket:
            self.init_connection()
        if auth and not self.auth_token:
            self.authorize()
        msg = self.gen_request(method, auth, **kwargs)
        if method == 'injectMarker':
            self.marker_dict[self.id_sequence] = "sent"
        self.websocket.send(msg)
        if wait:
            logger.debug("data sent; awaiting response")
            resp = self.websocket.recv()
            logger.debug(f"raw response received: {resp}")
            if 'error' in resp:
                logger.warning(
                    f"Got error in {method} with params {kwargs}:\n{resp}")
                raise CortexApiException(resp)
            resp = json.loads(resp)
            if callback:
                callback(resp)
            return resp
        return None

    def init_connection(self):
        """ Open a websocket and connect to cortex.  """
        self.websocket = websocket.WebSocket(
            sslopt={"cert_reqs": ssl.CERT_NONE})
        self.websocket.connect(self.CORTEX_URL, timeout=60)

    def ws_listen(self):
        self.running = True
        while self.running:
            try:
                result = json.loads(self.websocket.recv())
                # if inject marker response save marker_id
                result_id = result.get("id", False)
                if result_id and result['id'] in self.marker_dict.keys():
                    marker = (result.get("result", {})
                                 .get("marker", {}))
                    if marker:
                        marker_id = marker.get("uuid", "")
                        label = marker.get("label", "")
                        if marker_id and label:
                            del self.marker_dict[result_id]
                            self.marker_dict[label] = marker_id
                        else:
                            logger.warning(
                                "Unable to save marker_id: "
                                f"'{marker_id}' for label: '{label}'")
                elif result.get('eeg', False):  #EEG data
                    if EEG_ON:
                        logger.debug(f"result: {result}")
                        self.timestamps.append(result['time'])
                        row = result['eeg']
                        if row[self.marker_idx]:
                            self.marker_buffer.append(row[self.marker_idx][0]['value'])
                        if self.marker_buffer:
                            row.append(self.marker_buffer.pop(0))
                        else:
                            row.append(0)
                        self.data.append(row)
                else:
                    logger.debug(f'unhandled cortex response:\n{result}')
            except Exception as e:
                import traceback
                logger.error(traceback.format_exc())
                logger.error("maybe the websocket was closed" + str(e))
        if EEG_ON:
            df = pd.DataFrame(self.data, columns=self.columns)
            df.insert(0, 'timestamp', self.timestamps)
            df.to_csv(f"eeg_data_{self.timestamps[0]}.csv.gz", compression='gzip', index=False)
        logger.debug("Finished listening")

    def to_epoch(self, t=None, delta_time=0):
        """
        Takes either number of seconds or milliseconds since 1st of Jan 1970
        or a datetime object and outputs the number of milliseconds since Jan
        1970
        Parameters:
            t: input time; defaults to int(time.time()*1000)
            delta_time: optional time in seconds to add to the time. This is to
            add the time until the next screen flip (normally between 16 and 8 ms
        """
        if t is None:
            current_time = time.perf_counter() + self.tt0
            return int((current_time+delta_time)*1000)
        if isinstance(t, str) and t.isnumeric():
            t = float(t)
        if isinstance(t, float) or isinstance(t, int):
            if t > MS_SEC_THRESHOLD:
                return int(t + delta_time*1000)
            return int((t+delta_time) * 1000)
        elif isinstance(t, datetime.datetime):
            if t.tzinfo:
                return int((t.timestamp()+delta_time) * 1000)
            else:
                raise CortexTimingException(
                    "datetime without timezone will not convert correctly")
        else:
            raise CortexTimingException(f"Unable to interpret time: '{t}'")

    def set_client_id_and_secret(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    @staticmethod
    def parse_client_id_file(client_id_file_path=None):
        """
        Parse a client_id file for client_id and client secret.

        Parameter:
            client_id_file_path: absolute path to a client_id file

        We expect the client_id file to have the format:
        ```
        # optional comments start with hash
        client_id Jj2RihpwD6U3827GZ7J104URd1O9c0ZqBZut9E0y
        client_secret abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN
        ```
        """
        home = str(Path.home())
        if client_id_file_path is None:
            client_id_file_path = ".emotiv_creds"
            client_id_file_path = os.path.join(home, client_id_file_path)
        client_id = None
        client_secret = None
        if not os.path.exists(client_id_file_path):
            error_str = ("File {} does not exist. Please add Cortex app client"
                         "id and secret into '.emotiv_creds' file in home " 
                         "directory")
            raise OSError(error_str.format(client_id_file_path))
        with open(client_id_file_path, 'r') as client_id_file:
            for line in client_id_file:
                line = line.strip()
                if line.startswith('#'):
                    continue
                if len(line) == 0:
                    continue
                (key, val) = line.split(' ')
                if key == 'client_id':
                    client_id = val.strip()
                elif key == 'client_secret':
                    client_secret = val.strip()
                else:
                    raise ValueError(
                        f'Found invalid key "{key}" while parsing '
                        f'client_id file {client_id_file_path}')

        if not client_id or not client_secret:
            raise ValueError(
                f"Did not find expected keys in client_id file "
                f"{client_id_file_path}")
        return client_id, client_secret

    def gen_request(self, method, auth, **kwargs):
        """
        Generate a JSON request formatted for Cortex.

        Parameters:
            method: method name as a string
            auth: boolean indicating whether or not authentication is required
                for this method (may generate an additional call to
                authorize())
            **kwargs: all other keyword arguments become parameters in the
                request.
        """
        self.id_sequence += 1
        params = {key: value for (key, value) in kwargs.items()}
        if auth and self.auth_token:
            params['cortexToken'] = self.auth_token
        request = json.dumps(
            {'jsonrpc': "2.0",
             'method': method,
             'params': params,
             'id': self.id_sequence
             })
        logger.debug(f"Sending request:\n{request}")
        return request

    def authorize(self, license_id=None, debit=1):
        """
        Generate an authorization token, required for most actions.
        Requires a valid license file, that the user be logged in via
        the Emotiv App, and that the user has granted access to this app.

        Optionally, a license_id can be specified to allow sharing a
        device-locked license across multiple users.

        Parameters:
            license_id (optional): a specific license to be used with the app.
                Can specify another user's license.
            debit (optional): number of sessions to debit from the license
        """
        params = {'clientId': self.client_id,
                  'clientSecret': self.client_secret}
        if license_id:
            params['license_id'] = license_id
        if debit:
            params['debit'] = debit
        try:
            resp = self.send_wait_command('authorize', auth=False, **params)
        except CortexApiException as e:
            msg = json.loads(str(e))['error']['message'].lower()
            if "no access rights" in msg:
                raise CortexApiException("Please open the EmotivApp and grant "
                                         "permission to your applicationId")
            else:
                raise CortexApiException(msg)
        logger.debug(f"{__name__} resp:\n{resp}")
        self.auth_token = resp['result']['cortexToken']


    ##
    # Here down are cortex specific commands
    # Each of them is documented thoroughly in the API documentation:
    # https://emotiv.gitbook.io/cortex-api
    ##
    def inspectApi(self):
        """ Return a list of available cortex methods """
        resp = self.send_wait_command('inspectApi', auth=False)
        logger.debug(f"InspectApi resp:\n{resp}")

    def get_cortex_info(self):
        resp = self.send_wait_command('getCortexInfo', auth=False)
        logger.debug(f"{__name__} resp:\n{resp}")

    def flush_websocket(self):
        self.send_command('getCortexInfo', auth=False)

    def get_license_info(self):
        resp = self.send_wait_command('getLicenseInfo')
        logger.debug(f"{__name__} resp:\n{resp}")

    def query_headsets(self):
        resp = self.send_wait_command('queryHeadsets', auth=False)
        self.headsets = [h['id'] for h in resp['result']]
        logger.debug(f"{__name__} found headsets {self.headsets}")
        logger.debug(f"{__name__} resp:\n{resp}")

    def get_user_login(self):
        self.send_wait_command('getUserLogin', auth=False,
                               callback=self.get_user_login_cb)

    @staticmethod
    def get_user_login_cb(resp):
        """ Example of using the callback functionality of send_command """
        resp = resp['result']
        if len(resp) == 0:
            logger.debug(resp)
            raise CortexApiException(
                f"No user logged in! Please log in with the Emotiv App")
        resp = resp[0]
        if 'loggedInOSUId' not in resp:
            logger.debug(resp)
            raise CortexApiException(
                f"No user logged in! Please log in with the Emotiv App")
        if resp['currentOSUId'] != resp['loggedInOSUId']:
            logger.debug(resp)
            raise CortexApiException(
                f"Cortex is already in use by {resp.loggedInOSUsername}")
        logger.debug(f"{__name__} resp:\n{resp}")

    def has_access_right(self):
        params = {'clientId': self.client_id,
                  'clientSecret': self.client_secret}
        resp = self.send_wait_command('requestAccess', auth=False, **params)
        logger.debug(f"{__name__} resp:\n{resp}")

    def request_access(self):
        params = {'clientId': self.client_id,
                  'clientSecret': self.client_secret}
        resp = self.send_wait_command('requestAccess', auth=False, **params)
        logger.debug(f"{__name__} resp:\n{resp}")

    def control_device(self, command, headset_id=None,
                       flex_mapping=None):
        if not headset_id:
            headset_id = self.headsets[0]
        params = {'headset': headset_id,
                  'command': command}
        if flex_mapping:
            params['mappings'] = flex_mapping
        resp = self.send_wait_command('controlDevice', **params)
        logger.debug(f"{__name__} resp:\n{resp}")

    def create_session(self, activate, headset_id=None):
        status = 'active' if activate else 'open'
        if not headset_id:
            headset_id = self.headsets[0]
        logger.debug(f"Connecting to headset: {headset_id}")
        params = {'cortexToken': self.auth_token,
                  'headset': headset_id,
                  'status': status}
        try:
            resp = self.send_wait_command('createSession', **params)
        except CortexApiException as e:
            # msg = json.loads(str(e))['error']['message'].lower()
            code = json.loads(str(e))['error']['code']
            if code == -32004:
                raise CortexNoHeadsetException("Please connect the headset using "
                                         "EmotivApp or EmotivPro")
        self.session_id = resp['result']['id']
        logger.debug(f"{__name__} resp:\n{resp}")

    def create_record(self, title=None):
        if not title:
            time_str = datetime.datetime.now().isoformat()
            title = f'Psychopy recording ' + time_str
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id,
                  'title': title}
        resp = self.send_wait_command('createRecord', **params)
        logger.debug(f"{__name__} resp:\n{resp}")
        return resp

    def stop_record(self):
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id}
        resp = self.send_wait_command('stopRecord', **params)
        logger.debug(f"{__name__} resp:\n{resp}")
        return resp

    def close_session(self):
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id,
                  'status': 'close'}
        resp = self.send_wait_command('updateSession', **params)
        logger.debug(f"{__name__} resp:\n{resp}")
        self.disconnect()

    def inject_marker(self, label='', value=0, port='psychopy',
                      t=None, delta_time=None):
        ms_time = self.to_epoch(t,delta_time)
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id,
                  'label': label,
                  'value': value,
                  'port': port,
                  'time': ms_time}
        self.send_command('injectMarker', **params)

    def update_marker(self, label= None, t=None, delta_time=None):
        ms_time = self.to_epoch(t, delta_time)
        marker_id = self.marker_dict.get(label, None)
        if marker_id is None:
            raise Exception("no marker with that label")
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id,
                  'markerId': marker_id,
                  'time': ms_time}
        self.send_command('updateMarker', **params)
        del self.marker_dict[label]

    def subscribe(self, streamList):
        params = {'cortexToken': self.auth_token,
                  'session': self.session_id,
                  'streams': streamList}
        resp = self.send_wait_command('subscribe', **params)
        logger.debug(f"subscribe response: {resp}")
        if resp.get('result', {}).get('failure', []):
            raise CortexApiException(resp['result']['failure'])
        else:
            if resp.get('result', {}).get('success', []):
                # logger.debug(f"Success: {resp['result']['success']}")
                if resp['result']['success'][0].get('cols'):
                    self.columns = resp['result']['success'][0]['cols']
                    self.columns.append('MARKER_VALUE')
                    self.marker_idx = self.columns.index('MARKERS')
                else:
                    logger.debug("No columns")
            else:
                logger.debug("No success")
        logger.debug(f"subscribe response {resp}")
        return resp


    def start_listening(self):
        self.running = True
        listen_ws = threading.Thread(target=self.ws_listen)
        listen_ws.start()
        return listen_ws

    def stop_listening(self):
        self.running = False
        self.flush_websocket()  #

    def disconnect(self):
        self.stop_listening()
        time.sleep(2)
        self.websocket.close()


if __name__ == "__main__":
    cortex = Cortex()
    cortex.inject_marker(label="test_marker", value=4, port="psychpy")
    time.sleep(10)
    cortex.update_marker(label="test_marker")
