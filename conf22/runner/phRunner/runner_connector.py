import phantom.app as phantom
from phantom.action_result import ActionResult
from datetime import datetime, timedelta
import json
import requests


class RunnerConnector(phantom.BaseConnector):

    is_polling_action = False
    
    def __init__(self):
        super(RunnerConnector, self).__init__()
        return
    
    def __print(self, value, is_debug):
        print_debug = False
        try:
            print_debug = self.get_config()['debug']
        except:
            pass
        message = 'Failed to cast message to string'
        try:
            message = str(value)
        except:
            pass
        if print_debug or self.is_polling_action:
            self.debug_print(self.__class__.__name__, message)
            self.save_progress(message)
        elif not is_debug:
            self.save_progress(message)

    def _get_base_url(self):
        self.__print("_get_base_url()", True)
        port = 443
        try:
            port = self.get_config()['https_port']
        except:
            pass
        return f'https://127.0.0.1:{port}'

    def _get_rest_data(self, endpoint):
        try:
            url = f'{self._get_base_url()}/{endpoint}'
            self.__print(url, True)
            response = phantom.requests.get(url, verify=False)
            content = json.loads(response.text)
            code = response.status_code
            if 199 < code < 300:
                if 'data' in content and 'container/' not in url:
                    return content['data']
                else:
                    return content
            else:
                return None
        except:
            return None

    def _post_rest_data(self, endpoint, dictionary):
        try:
            url = f'{self._get_base_url()}/{endpoint}'
            self.__print(url, True)
            data = json.dumps(dictionary)
            response = phantom.requests.post(url, data=data, verify=False)
            content = response.text
            code = response.status_code
            if 199 < code < 300:
                if 'data' in content:
                    return content['data']
                else:
                    return content
            else:
                return None
        except:
            return None

    def _create_artifact(self, comment, unit, duration, playbook, scope):
        self.__print('_create_artifact()', True)
        artifact_dict = { "cef": { "comment": comment,
                                "durationUnit": unit,
                                "duration": duration,
                                "playbook": playbook,
                                "scope": scope },
                          "container_id": self.get_container_id(),
                          "label": "pending",
                          "name": "scheduled playbook",
                          "source_data_identifier": f'runner-{datetime.now()}-{self.get_container_id()}',
                          "run_automation": False }

        self.__print(f'Posting artifact: {artifact_dict}', True)
        uri = "rest/artifact"
        response = self._post_rest_data(uri, artifact_dict)
        if response is not None:
            return True
        else:
            return False

    def _disable_artifact(self, container):
        self.__print('_disable_artifact()', True)
        uri = f'rest/container/{container}/artifacts?_filter_name=%22scheduled playbook%22&_filter_label=%22pending%22'
        response = self._get_rest_data(uri)
        update_data = {}
        update_data['label'] = 'halted'
        for artifact in response['data']:
            update_data['id'] = artifact['id']
            uri = f'rest/artifact/{artifact["id"]}'
            response = self._post_rest_data(uri)
        return

    def _add_waiting_tag(self):
        self.__print('_add_waiting_tag()', True)
        uri = f'rest/container/{self.get_container_id()}'
        response = self._get_rest_data(uri)
        self.__print(response, True)
        tags = response['tags']
        if 'waiting' not in tags:
            tags.append('waiting')
        update_data = {}
        update_data['tags'] = tags
        response = self._post_rest_data(uri, update_data)
        return

    def _delete_waiting_tag(self, container):
        self.__print('_delete_waiting_tag()', True)
        uri = f'rest/container/{container}'
        response = self._get_rest_data(uri)
        tags = response['tags']
        if 'waiting' in tags:
            tags.remove('waiting')
        update_data = {}
        update_data['tags'] = tags
        response = self._post_rest_data(uri, update_data)
        return

    def _is_playbook_valid(self, artifact, container):
        self.__print('_is_playbook_valid()', True)
        is_valid = False
        playbook = self._playbook_exists(artifact['cef']['playbook'])
        if playbook is not None and playbook != []:
            if container['label'] in playbook[0]['labels'] or "*" in playbook[0]['labels']:
                is_valid = True
        return is_valid

    def _playbook_exists(self, playbook):
        self.__print('_playbook_exists()', True)
        playbook_json = None
        if '/' not in playbook:
            return playbook_json
        playbook_string = playbook.split('/')
        repo = playbook_string[0]
        playbook = playbook_string[1]
        uri = f'rest/scm?page_size=0&_filter_name="{repo}"'
        repo_data = self._get_rest_data(uri)
        if repo_data is not None and repo_data != []:
            uri = f'rest/playbook?page_size=1&_filter_name="{playbook}"&_filter_scm={repo_data[0]["id"]}'
            playbook_json = self._get_rest_data(uri)
        return playbook_json

    def _get_all_pending_artifacts(self):
        self.__print('_get_all_pending_artifacts()', True)
        try:
            uri = 'rest/artifact?page_size=0&_filter_label="pending"&_filter_name__contains="scheduled playbook"'
            pending_artifacts = self._get_rest_data(uri)
            return pending_artifacts
        except Exception as e:
            self.__print('Failed to retrieved pending scheduled playbooks', False)
            self.__print(e, False)
            return None

    def _is_expired(self, artifact):
        self.__print('_is_expired()', True)
        is_expired = False
        unit = artifact['cef']['durationUnit']
        duration = artifact['cef']['duration']
        if unit == 'Minutes':
            expiration = datetime.strptime(artifact['create_time'], '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(minutes=int(duration))
        elif unit == 'Hours':
            expiration = datetime.strptime(artifact['create_time'], '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(hours=int(duration))
        elif unit == 'Days':
            expiration = datetime.strptime(artifact['create_time'], '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(days=int(duration))
        self.__print(f'now: {datetime.now()}', True)
        self.__print(f'expiration: {expiration}', True)
        self.__print(f'creation: {artifact["create_time"]}', True)
        if expiration <= datetime.now():
            is_expired = True
        return is_expired

    def _get_container(self, artifact):
        self.__print('_get_container()', True)
        uri = f'rest/container/{artifact["container"]}'
        container = self._get_rest_data(uri)
        return container

    def _run_playbook(self, artifact):
        self.__print('_run_playbook()', True)
        success = False
        uri = 'rest/playbook_run'
        data = { "container_id": artifact['container'], "playbook_id": artifact['cef']['playbook'], "scope": artifact['cef']['scope'], "run": "true" }
        if self._post_rest_data(uri, data) is not None:
            success = True
        return success

    def _is_playbook_pending(self, artifact):
        self.__print('_is_playbook_pending()', True)
        is_playbook_pending = False
        uri = f'rest/container/{artifact["container"]}/artifacts?page_size=0&_filter_label="pending"&_filter_name__contains="scheduled playbook"'
        playbooks = self._get_rest_data(uri)
        if playbooks['data'] != []:
            is_playbook_pending = True
        return is_playbook_pending

    def _delete_tag(self, state, artifact):
        self.__print('_delete_tag()', True)
        uri = f'rest/container/{artifact["container"]}'
        response = self._get_rest_data(uri)
        tags = []
        tags.extend(response['tags'])
        self.__print(tags, True)
        if state in tags:
            tags.remove(state)
        update_data = {}
        update_data['tags'] = tags
        response = self._post_rest_data(uri, update_data)
        return

    def _update_artifact(self, state, artifact):
        self.__print('_update_artifact()', True)
        update_data = {}
        update_data['cef'] = {}
        update_data['cef'].update(artifact['cef'])
        update_data['cef']['exeComment'] = f'Execution run at {datetime.now()}'
        update_data['label'] = state
        uri = f'rest/artifact/{artifact["id"]}'
        self._post_rest_data(uri, update_data)
        return

    def _handle_test_connectivity(self, param):
        self.__print("_handle_test_connectivity", True)
        action_result = self.add_action_result(ActionResult(dict(param)))
        test_url = f'{self._get_base_url()}/rest/version'
        self.__print(f'Attempting http get for {test_url}', False)
        response = None
        try:
            response = phantom.requests.get(test_url, verify=False)
            self.__print(response.status_code, True)
        except:
            pass
        if response and 199 < response.status_code < 300:
            version = json.loads(response.text)['version']
            self.__print(f'Successfully retrieved platform version: {version}', False)
            self.__print('Passed connection test', False)
            return action_result.set_status(phantom.APP_SUCCESS)
        else:
            self.__print(f'Failed to reach test url: {test_url}\nCheck your hostname config value', False)
            self.__print('Failed connection test', False)
            return action_result.set_status(phantom.APP_ERROR, f'Failed to reach test url {test_url}')

    def _handle_schedule_playbook(self, param):
        self.__print('_handle_schedule_playbook()', True)
        try:
            self.__print('Building standard delayed execution artifact', True)
            comment = param.get('delay_purpose')
            unit = param.get('duration_unit')
            duration = param.get('delay_duration')
            playbook = param.get('playbook')
            scope = param.get('playbook_scope')
            if scope == "artifact":
                ids = []
                ids.append(param.get('artifact_id'))
                scope = ids
            if not self._create_artifact(comment, unit, duration, playbook, scope):
                self.set_status_save_progress(phantom.APP_ERROR, 'Artifact creation failed')
                return phantom.APP_ERROR
            self._add_waiting_tag()
            self.set_status_save_progress(phantom.APP_SUCCESS, 'Successfully completed execution delay')
            return phantom.APP_SUCCESS
        except Exception as e:
            self.__print('_handle_schedule_playbook() failed', False)
            self.__print(e, False)
            self.set_status_save_progress(phantom.APP_ERROR, e)
            return phantom.APP_ERROR

    def _handle_clear_scheduled_playbooks(self, param):
        self.__print('_handle_clear_scheduled_playbooks()', True)
        try:
            self.__print('Removing execution parameters', True)
            container_identifier = param.get('container_identifier')
            if container_identifier is None or container_identifier == '':
                container_identifier = self.get_container_id()
            self._delete_waiting_tag(container_identifier)
            self._disable_artifact(container_identifier)
            self.set_status_save_progress(phantom.APP_SUCCESS, 'Successfully halted execution')
            return phantom.APP_SUCCESS
        except Exception as e:
            self.__print('_handle_clear_scheduled_playbooks() failed', False)
            self.__print(e, False)
            self.set_status_save_progress(phantom.APP_ERROR, e)
            return phantom.APP_ERROR

    def _handle_on_poll(self, param):
        self.__print('_handle_on_poll()', True)
        self.is_polling_action = True
        action_result = self.add_action_result(ActionResult(dict(param)))
        try:
            limit = self.get_config()['playbook_limit']
        except:
            limit = 4
        try:
            executions = 0
            for artifact in self._get_all_pending_artifacts():
                self.__print(f'Processing artifact {artifact["id"]}', True)
                container = self._get_container(artifact)
                if self._is_expired(artifact):
                    self.__print(f'artifact {artifact["id"]} is expired', True)
                    if self._is_playbook_valid(artifact, container):
                        self.__print('playbook is valid', True)
                        executions += 1
                        self._run_playbook(artifact)
                        self._update_artifact('complete', artifact)
                    else:
                        self.__print(f'playbook is invalid: {artifact["cef"]["playbook"]}', False)
                        self._update_artifact('invalid playbook', artifact)
                    if self._is_playbook_pending(artifact):
                        self.__print('playbooks pending', True)
                    else:
                        self.__print('no playbooks pending', True)
                        self._delete_tag('waiting', artifact)
                else:
                    self.__print(f'artifact {artifact["id"]} is not expired yet', True)
                if executions > limit:
                    break
            self.__print(f'{executions} playbooks executed', False)
            action_result.set_status(phantom.APP_SUCCESS, f'{executions} playbooks executed')
        except Exception as e:
            self.__print('Error processing artifacts and playbooks', False)
            self.__print(e, False)
            self.set_status(phantom.APP_ERROR, 'Error processing artifacts and playbooks')
            return phantom.APP_ERROR

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        action_id = self.get_action_identifier()
        
        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'schedule_playbook':
            ret_val = self._handle_schedule_playbook(param)

        if action_id == 'clear_scheduled_playbooks':
            ret_val = self._handle_clear_scheduled_playbooks(param)

        if action_id == 'on_poll':
            ret_val = self._handle_on_poll(param)

        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)

        return ret_val
